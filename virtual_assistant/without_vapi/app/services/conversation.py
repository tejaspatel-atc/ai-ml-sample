import asyncio
from threading import Event
from typing import AsyncIterator, Dict, List, Optional

from fastapi.websockets import WebSocket

from app.logger import logger
from app.services.deepgram import SpeechToText, TextToSpeech
from app.services.openai import OpenAIAssistant
from app.services.twilio import TwilioCallManager
from app.settings import settings


class ConversationManager:

    def __init__(
        self, websocket: WebSocket, bot_id: str, bot_details: Dict, call_sid: str, stream_sid: str
    ) -> None:
        self._websocket = websocket
        self.active_connections: List[WebSocket] = []
        self.twilio_call_manager = TwilioCallManager(self._websocket)

        self._stop_events: Dict[str, Event] = {}
        self._stt_service = SpeechToText()
        self._tts_service = TextToSpeech()
        self._stream_sid = stream_sid
        self._call_sid = call_sid

        self._transcription_and_interruption_worker_task: Optional[asyncio.Task] = None
        self._conversation_worker_task: Optional[asyncio.Task] = None

        # Fetch bot details from Supabase on connection initialization
        self.bot_data = bot_details
        self.open_ai_assistant_obj = OpenAIAssistant(
            bot_id,
            self.bot_data["gpt_assistant_id"],
            self.bot_data["gpt_vector_store_id"],
        )

        self._transcriptions: asyncio.Queue[str] = asyncio.Queue()
        self._sent_initial_message = asyncio.Event()
        self._interrupt_event = asyncio.Event()
        self._processing_event = asyncio.Event()
        self.is_active = asyncio.Event()

    async def start(self) -> None:
        self._processing_event.clear()
        self._sent_initial_message.clear()

        asyncio.create_task(self._send_initial_message())  # Keep as a task
        await asyncio.gather(self._stt_service.start(), self.open_ai_assistant_obj.create_thread())

        self._transcription_and_interruption_worker_task = asyncio.create_task(
            self._transcription_and_interruption_worker()
        )
        self._conversation_worker_task = asyncio.create_task(self._conversation_worker())
        self.is_active.set()

        logger.info("Started conversation manager")

    async def stop(self) -> None:
        await self._stt_service.stop()
        if self._transcription_and_interruption_worker_task:
            self._transcription_and_interruption_worker_task.cancel()
        if self._conversation_worker_task:
            self._conversation_worker_task.cancel()
        self.is_active.clear()
        logger.info("Stopped conversation manager")

    async def receive_audio(self, chunk: bytes) -> None:
        await self._stt_service.send_chunk(chunk)

    async def get_chatgpt_response(self, content: str) -> AsyncIterator[str]:
        # Start creating the thread message with the content
        await self.open_ai_assistant_obj.create_thread_message(content=content)

        # Stream the response asynchronously
        async for content_chunk in self.open_ai_assistant_obj.run(self._interrupt_event):
            yield content_chunk

    async def _conversation_worker(self) -> None:
        while self.is_active.is_set():
            await asyncio.sleep(0)
            if not self._transcriptions.empty():
                self._processing_event.set()

                transcription = await self._transcriptions.get()
                response = self.get_chatgpt_response(transcription)
                audio_stream = self._tts_service.generate_audio(content=response)

                speech_length_seconds = 0.0

                async for chunk in audio_stream:
                    if not self._interrupt_event.is_set():
                        speech_length_seconds += len(chunk) / settings.SAMPLE_RATE
                        await self.twilio_call_manager.send_chunk(
                            stream_sid=self._stream_sid, chunk=chunk
                        )
                        await self.twilio_call_manager.send_mark(
                            stream_sid=self._stream_sid, mark_name=self._stream_sid
                        )
                    else:
                        logger.info("I'm interrupting from here 4")
                        await self.twilio_call_manager.clear_buffer(stream_sid=self._stream_sid)
                        break

                wait_time = speech_length_seconds - settings.SPEECH_DELAY_SECONDS
                await asyncio.sleep(max(wait_time, 0))
                self._processing_event.clear()

    async def _transcription_and_interruption_worker(self) -> None:
        while self.is_active.is_set():
            # ========= INTERRUPTION LOGIC =========
            await asyncio.sleep(0)
            if (
                self._stt_service.is_speaking
                and not self._stt_service.is_speech_final
                and not self._interrupt_event.is_set()
                and self._processing_event.is_set()
            ):
                transcription = self._stt_service.get_transcription()
                if len(transcription.split(" ")) > settings.INTERRUPTION_WORD_COUNT:
                    logger.info("User started speaking")
                    self._interrupt_event.set()
                    self._processing_event.clear()
                    await self._cancel_current_task()
            # ========= INTERRUPTION LOGIC =========

            # ========= TRANSCRIPTION AND AGENT SPEAKING LOGIC =========
            await asyncio.sleep(0)
            if self._stt_service.is_speech_final:
                # Get transcription
                transcription = self._stt_service.get_transcription()
                logger.info(f"Final Transcription: {transcription}")
                # if processing event is set | If there is something in the queue
                if self._processing_event.is_set():
                    # Clear twilio buffer if there is something still processing
                    # And received more than two words
                    logger.info("Got a new transcription while processing")
                    self._interrupt_event.set()
                    self._processing_event.clear()
                    await self._cancel_current_task()
                await self._transcriptions.put(transcription)

                self._processing_event.clear()
                self._interrupt_event.clear()

    # ================== New Optimized Code ==================
    async def _cancel_current_task(self) -> None:
        if self._conversation_worker_task is not None and not (
            self._conversation_worker_task.cancelled() or self._conversation_worker_task.done()
        ):
            logger.info("Cancelling the current conversation worker task")
            self._conversation_worker_task.cancel()
        await self.twilio_call_manager.clear_buffer(stream_sid=self._stream_sid)

    # ================== End of New Optimized Code ==================

    async def _is_bot_available(self) -> None:
        if not self.bot_data:
            return False
        elif (
            not self.bot_data.get("active", False)
            or self.bot_data.get("billing_status") != "active"
        ):
            return False
        return True

    async def _send_initial_message(self) -> None:
        audio_stream = self._tts_service.generate_audio_stream_from_text(
            self.bot_data.get("greeting") or "Hello, how can I help you?"
        )
        await self.twilio_call_manager.stream_audio(
            stream_sid=self._stream_sid, audio_stream=audio_stream
        )
        self._sent_initial_message.set()

    async def _end_call(self, end_call_message: str = "Bye, Bye!") -> None:
        audio_stream = self._tts_service.generate_audio_stream_from_text(end_call_message)
        await self.twilio_call_manager.stream_audio(
            stream_sid=self._stream_sid, audio_stream=audio_stream
        )
        # Wait for 3 seconds because stream audio takes time to speak
        await asyncio.sleep(3)
        await self.twilio_call_manager.end_call(self._call_sid)
