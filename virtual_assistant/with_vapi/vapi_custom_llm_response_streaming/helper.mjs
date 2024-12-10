import { EventEmitter } from "node:events";
import { openai, regex, supabase } from "./config.mjs";
import * as customFunctions from "./customFunction.mjs";

export const handleStreamError = (responseStream, message, isForChat = true) => {
    if (isForChat) {
        responseStream.write(message);
    } else {
        responseStream.write(
            `data: ${JSON.stringify({
                choices: [
                    {
                        index: 0,
                        delta: {
                            content: `${message}[Done]\n\n`,
                        },
                    },
                ],
            })}\n\n`
        );
    }
    responseStream.end();
};

export const insertMessage = async (messageData) => {
    await supabase.from("messages").insert(messageData);
};

export const createOrRetrieveThread = async (gptVectorStoreId, threadId) => {
    if (!threadId || threadId.trim() === "" || threadId === "null" || threadId === "undefined") {
        const toolResources = gptVectorStoreId
            ? { file_search: { vector_store_ids: [gptVectorStoreId] } }
            : null;
        return await openai.beta.threads.create({ tool_resources: toolResources });
    }
    return await openai.beta.threads.retrieve(threadId);
};

export const createThreadRun = async (threadId, gptAssistantId, additionalInstructions) => {
    return await openai.beta.threads.runs.create(threadId, {
        assistant_id: gptAssistantId,
        additional_instructions: additionalInstructions,
        metadata: { chatType: "Chat" },
        stream: true,
    });
};

class StreamingEventHandler extends EventEmitter {
    constructor(
        client,
        responseStream,
        isForChat,
        callConversation,
        queryStringParameters = {},
        sessionId = null,
        botId = null
    ) {
        super();
        this.client = client;
        this.responseStream = responseStream;
        this.isForChat = isForChat;
        this.queryStringParameters = queryStringParameters;
        this.sessionId = sessionId;
        this.botId = botId;
        this.callConversation = callConversation;
    }

    async onEvent(event) {
        try {
            if (event.event === "thread.run.requires_action") {
                await this.handleActionRequired(event.data, event.data.id, event.data.thread_id);
            } else if (event.event === "thread.message.delta") {
                this.handleMessageDelta(event);
            } else if (event.event === "thread.message.completed") {
                await this.handleMessageCompleted(event);
            } else if (event.event === "thread.run.completed") {
                this.responseStream.end();
            }
        } catch (error) {
            console.error("Error handling stream event: ", error);
            await this.client.beta.threads.runs.cancel({
                thread_id: event.data.thread_id,
                run_id: event.data.id,
            });
            throw error;
        }
    }

    handleMessageDelta(event) {
        const originalMessage = event.data.delta.content[0].text.value;
        const modifiedMessage = regex ? originalMessage.replace(regex, "") : originalMessage;

        if (this.isForChat) {
            this.responseStream.write(modifiedMessage);
        } else {
            this.responseStream.write(
                `data: ${JSON.stringify({
                    choices: [
                        {
                            index: 0,
                            delta: {
                                content: modifiedMessage,
                            },
                        },
                    ],
                })}\n\n`
            );
        }
    }

    async handleMessageCompleted(event) {
        console.info("Message Completed");
        if (this.isForChat) {
            await insertMessage({
                message: event.data.content[0].text.value.replace(regex, ""),
                message_type: "bot_answer",
                user_id: this.queryStringParameters.user_id || "anonymous",
                user_type: this.queryStringParameters.user_type || "anonymous",
                bot_id: this.botId,
                channel: this.queryStringParameters.channel || "text",
                user_phone_number: this.queryStringParameters.user_phone_number || "",
                session_id: this.sessionId,
                thread_id: event.data.thread_id,
            });
            this.responseStream.write(
                "\n" +
                    JSON.stringify({
                        status: "done",
                        threadId: event.data.thread_id,
                        sessionId: this.sessionId,
                    }) +
                    "\n"
            );
        } else {
            this.responseStream.write("data: [DONE]\n\n");
        }
    }

    async handleActionRequired(data, runId, threadId) {
        try {
            console.info("Action Required");
            const toolCalls = data.required_action.submit_tool_outputs.tool_calls;
            const toolOutputs = await Promise.all(
                toolCalls.map(async (toolCall) => {
                    let output;
                    try {
                        const args = JSON.parse(toolCall.function.arguments);
                        console.log("Args", args);
                        output = await customFunctions[toolCall.function.name]({
                            sessionId: this.sessionId,
                            ...args,
                            botId: this.botId,
                            isForChat: this.isForChat,
                            callConversation: this.callConversation,
                        });
                    } catch (e) {
                        console.error(`Error in function ${toolCall.function.name}:`, e);
                        output = "Unexpected Error Occurred. Please try again later.";
                    }
                    return { tool_call_id: toolCall.id, output };
                })
            );
            await this.submitToolOutputs(toolOutputs, runId, threadId);
        } catch (error) {
            console.error("Error processing required action:", error);
        }
    }

    async submitToolOutputs(toolOutputs, runId, threadId) {
        try {
            const stream = this.client.beta.threads.runs.submitToolOutputsStream(threadId, runId, {
                tool_outputs: toolOutputs,
            });
            for await (const event of stream) {
                this.emit("event", event);
            }
        } catch (error) {
            console.error("Error submitting tool outputs:", error);
        }
    }
}

export const handleStreamEvents = async ({
    client,
    stream,
    responseStream,
    isForChat = true,
    queryStringParameters = {},
    sessionId = null,
    botId = null,
    callConversation = [],
}) => {
    if (isForChat && (!queryStringParameters || !sessionId || !botId)) {
        throw new Error(
            "queryStringParameters, sessionId, and botId are required for chat events."
        );
    }
    const eventHandler = new StreamingEventHandler(
        client,
        responseStream,
        isForChat,
        callConversation,
        queryStringParameters,
        sessionId,
        botId
    );
    eventHandler.on("event", eventHandler.onEvent.bind(eventHandler));
    for await (const event of stream) {
        eventHandler.emit("event", event);
    }
};
