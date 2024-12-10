import asyncio
import json
from pdb import run
from typing import Any, AsyncIterator, Dict, List, Literal, Optional

from openai import AsyncOpenAI, OpenAIError
from openai.types.beta.threads import RequiredActionFunctionToolCall, Run
from openai.types.beta.threads.run_submit_tool_outputs_params import ToolOutput

from app.logger import logger
from app.services import custom_functions
from app.settings import settings


class OpenAIAssistant:
    """
    Class to interact with OpenAI API for handling assistant conversations, including thread creation,
    message submission, and action processing.

    Attributes:
        bot_id: ID of the bot using the assistant.
        gpt_assistant_id: ID of the OpenAI GPT assistant.
        gpt_vector_store_id: Optional. ID for vector store, if applicable.
    """

    def __init__(
        self, bot_id: str, gpt_assistant_id: str, gpt_vector_store_id: Optional[str] = None
    ):
        """
        Initializes the OpenAIAssistant instance.

        Args:
            bot_id: ID of the bot.
            gpt_assistant_id: ID of the GPT assistant.
            gpt_vector_store_id: Optional vector store ID for advanced querying.
        """
        self.__client: AsyncOpenAI = AsyncOpenAI(api_key=settings.OPEN_AI_API_KEY)
        self.__assistant_id: str = gpt_assistant_id
        self.__bot_id: str = bot_id
        self.__vector_store_id: Optional[str] = gpt_vector_store_id
        self.__thread_id: Optional[str] = None
        self.__run_id: Optional[str] = None
        self.call_conversation: List[Dict[str, str]] = []

    def __append_call_conversation(self, role: Literal["user", "assistant"], content: str) -> None:
        """
        Appends the message to the call conversation log.

        Args:
            role: The role of the message sender, either 'user' or 'assistant'.
            content: The content of the message.
        """
        self.call_conversation.append({"role": role, "content": content})

    async def create_thread(self) -> None:
        """
        Creates a new thread for the assistant interaction.
        """
        try:
            thread = await self.__client.beta.threads.create()
            self.__thread_id = thread.id
        except OpenAIError as e:
            logger.error(f"Failed to create thread: {e}")
            raise

    async def create_thread_message(self, content: str) -> None:
        """
        Adds a user message to the current thread and appends it to the conversation log.

        Args:
            content: The content of the user's message.
        """
        try:
            self.__append_call_conversation("user", content)
            await self.__client.beta.threads.messages.create(
                self.__thread_id,
                role="user",
                content=content,
            )
        except OpenAIError as e:
            logger.error(f"Failed to send message: {e}")
            raise

    async def process_tool_call(self, tool_call: RequiredActionFunctionToolCall) -> Dict[str, Any]:
        """
        Processes an individual tool call from the required actions.

        Args:
            tool_call: A dictionary containing the tool call details.

        Returns:
            A dictionary containing the tool call ID and the result output.
        """
        try:
            args = json.loads(tool_call.function.arguments)
            logger.info(f"Processing tool call with args: {args}")
            function_name = tool_call.function.name

            # Fetching custom function based on tool call name
            if hasattr(custom_functions, function_name):
                function_to_call = getattr(custom_functions, function_name)
            else:
                raise ValueError(f"Function {function_name} not found")

            output = await function_to_call(
                name=args.get("name"),
                email=args.get("email"),
                phone=args.get("phone"),
                bot_id=self.__bot_id,
                call_conversation=self.call_conversation,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error processing tool call {tool_call['function']['name']}: {e}")
            output = "Unexpected Error Occurred. Please try again later."

        return {"tool_call_id": tool_call.id, "output": output}

    async def handle_action_required(self, data: Run) -> Optional[str]:
        """
        Handles required actions by processing tool calls and submitting outputs.

        Args:
            data: The event data containing required actions.

        Returns:
            Optional string of the assistant's response after processing tool outputs.
        """
        try:
            logger.info("Action Required: Processing tool calls.")
            tool_calls: List[RequiredActionFunctionToolCall] = (
                data.required_action.submit_tool_outputs.tool_calls
            )
            tool_outputs: List[ToolOutput] = await asyncio.gather(
                *[self.process_tool_call(tool_call) for tool_call in tool_calls]
            )
            return await self.submit_tool_outputs(tool_outputs)
        except Exception as e:
            logger.error(f"Error processing required action: {e}")
            return "Error processing required action."

    async def submit_tool_outputs(self, tool_outputs: List[ToolOutput]) -> Optional[str]:
        """
        Submits tool outputs and handles the response stream.

        Args:
            tool_outputs: A list of processed tool outputs.

        Returns:
            The final content response from the assistant.
        """
        try:
            stream: AsyncIterator[Run] = self.__client.beta.threads.runs.submit_tool_outputs_stream(
                run_id=self.__run_id,
                thread_id=self.__thread_id,
                tool_outputs=tool_outputs,
            )

            content = ""
            async with stream as stream:
                async for delta in stream.text_deltas:
                    content = content.__add__(delta)
            return content
        except OpenAIError as e:
            logger.error(f"Error submitting tool outputs: {e}")
            return None

    async def run(self, interrupt_event: asyncio.Event) -> AsyncIterator[str]:
        """
        Main method to process and handle the assistant's conversation in real-time.

        Args:
            interrupt_event: An asyncio event to detect if the conversation should be interrupted.

        Yields:
            The assistant's response as strings.
        """
        try:
            stream = await self.__client.beta.threads.runs.create(
                thread_id=self.__thread_id, assistant_id=self.__assistant_id, stream=True
            )

            buffer = ""
            delimiters = tuple(
                settings.OPEN_AI_DELIMITERS
            )  # Natural breakpoints for smoother speaking

            async for event in stream:
                self.__run_id = event.data.id

                # Handling interruption
                if interrupt_event and interrupt_event.is_set():
                    break

                match event.event:
                    case "thread.run.requires_action":
                        yield "I'm working on your request. Please wait..."
                        data = await self.handle_action_required(event.data)
                        yield data
                    case "thread.message.delta":
                        content = event.data.delta.content[0].text.value
                        if content:
                            buffer += content
                            if buffer.endswith(delimiters):
                                yield buffer.strip()
                                buffer = ""
                    case "thread.message.completed":
                        self.__append_call_conversation(
                            "assistant", event.data.content[0].text.value
                        )
                        if buffer:
                            yield buffer.strip()
                        self.__run_id = None
                        break

            if interrupt_event and interrupt_event.is_set():
                await self.__client.beta.threads.runs.cancel(
                    thread_id=self.__thread_id, run_id=self.__run_id
                )
                self.__run_id = None
        except OpenAIError as e:
            logger.error(f"OpenAI error during conversation run: {e}")
            yield "Error processing your request. Please try again later."
        except asyncio.CancelledError:
            logger.info("Conversation task was cancelled.")
            self.__run_id = None
