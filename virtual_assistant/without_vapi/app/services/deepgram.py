from typing import Any, AsyncGenerator, AsyncIterator

from deepgram import (
    AsyncLiveClient,
    DeepgramClient,
    DeepgramClientOptions,
    LiveOptions,
    LiveResultResponse,
    LiveTranscriptionEvents,
    SpeakOptions,
    SpeakWebSocketEvents,
)
from deepgram.clients.common.v1.options import TextSource

from app.logger import logger
from app.settings import settings


class SpeechToText:

    def __init__(
        self,
        encoding: str | None = settings.DEEPGRAM_ENCODING,
        sample_rate: int | None = settings.SAMPLE_RATE,
    ) -> None:
        self.is_speech_final = False
        self.is_speaking = False
        self._current_buffer = ""
        self._current_result: LiveResultResponse | None = None
        self._live_options = LiveOptions(
            language="en-US",
            model=settings.DEEPGRAM_SST_MODEL,
            encoding=encoding,
            sample_rate=sample_rate,
            channels=1,
            version="latest",
            punctuate=True,
            interim_results=True,
            endpointing="400",
            utterance_end_ms="1000",
            vad_events=True,
        )
        self._client = AsyncLiveClient(
            config=DeepgramClientOptions(
                api_key=settings.DEEPGRAM_SECRET_KEY,
                options={"termination_exception_send": "false"},
            )
        )
        self._client.on(LiveTranscriptionEvents.Transcript, self._on_message)
        self._client.on(LiveTranscriptionEvents.SpeechStarted, self._on_speech_started)
        self._client.on(LiveTranscriptionEvents.Error, self._on_error)
        self._client.on(LiveTranscriptionEvents.UtteranceEnd, self._on_utterance_end)

    async def start(self) -> bool:
        return await self._client.start(self._live_options)

    async def stop(self) -> bool:
        return await self._client.finish()

    async def send_chunk(self, chunk: bytes) -> None:
        await self._client.send(chunk)

    def get_transcription(self) -> str:
        """Get the current transcription and clear the buffer"""
        self.is_speech_final = False
        self.is_speaking = False
        transcription = self._current_buffer
        self._current_buffer = ""
        return transcription

    def _calculate_time_silent(self, result: LiveResultResponse) -> float:
        end = result.start + result.duration
        words = result.channel.alternatives[0].words
        if words and words[-1].end:
            return end - words[-1].end
        return result.duration

    def _is_speech_final(self, result: LiveResultResponse) -> bool:
        transcript = result.channel.alternatives[0].transcript
        time_silent = self._calculate_time_silent(result)
        return (
            bool(transcript)
            and result.speech_final
            and transcript.strip()[-1] in settings.PUNCTUATION_TERMINATORS
        ) or (
            not bool(transcript)
            and bool(self._current_buffer)
            and ((time_silent + result.duration) > settings.SILENCE_THRESHOLD)
        )

    def _is_speaking(self, result: LiveResultResponse) -> bool:
        """
        Set is speaking if there is a transcript in the response,
        the speech is not final, and is more than 3 words
        """
        transcript = result.channel.alternatives[0].transcript
        word_count = len(result.channel.alternatives[0].words)
        return bool(transcript) and word_count > settings.INTERRUPTION_WORD_COUNT

    async def _on_speech_started(self, *arg: Any, **kwargs: Any) -> None:
        if self._current_result:
            self.is_speaking = self._is_speaking(self._current_result)

    async def _on_error(self, *args: Any, **kwargs: Any) -> None:
        error = kwargs.get("error")
        self.is_speech_final = False
        self.is_speaking = False
        self._current_buffer = ""
        if error:
            logger.error(error)

    async def _on_utterance_end(self, *arg: Any, **kwargs: Any) -> None:
        if self._current_result:
            self.is_speech_final = self._is_speech_final(self._current_result)
            self.is_speaking = self._is_speaking(self._current_result)

    async def _on_message(self, *arg: Any, **kwargs: Any) -> None:
        result: LiveResultResponse | None = kwargs.get("result")
        if result:
            self._current_result = result
            self.is_speech_final = self._is_speech_final(result)
            self.is_speaking = self._is_speaking(result)
            if result.is_final:
                if len(self._current_buffer):
                    self._current_buffer += " "
                self._current_buffer += result.channel.alternatives[0].transcript


class TextToSpeech:
    def __init__(self):
        self.deepgram: DeepgramClient = DeepgramClient(
            api_key=settings.DEEPGRAM_SECRET_KEY,
            config=DeepgramClientOptions(
                api_key=settings.DEEPGRAM_SECRET_KEY,
                options={"termination_exception_send": "false"},
            ),
        )
        # Create a websocket connection to Deepgram
        self.dg_connection = self.deepgram.speak.websocket.v("1")
        self.dg_connection.on(SpeakWebSocketEvents.Open, self.on_open)
        self.dg_connection.on(SpeakWebSocketEvents.Close, self.on_close)

    def on_open(self, *args, **kwargs):
        # Log or inspect args to understand what is passed
        logger.info(f"WebSocket opened with args: {args}, kwargs: {kwargs}")

    def on_close(self, *args, **kwargs):
        # Log or inspect args to understand what is passed
        logger.info(f"WebSocket closed with args: {args}, kwargs: {kwargs}")

    @property
    def speak_options(self) -> SpeakOptions:
        return SpeakOptions(
            model=settings.DEEPGRAM_TTS_MODEL,
            encoding=settings.DEEPGRAM_ENCODING,
            container="none",
            sample_rate=settings.SAMPLE_RATE,
        ).__dict__

    async def generate_audio(
        self,
        content: AsyncIterator[str],  # Expecting an asynchronous iterator of string chunks
    ):
        async for string_chunk in content:  # Asynchronously iterate over content chunks
            response = self.deepgram.speak.v("1").stream_memory(
                TextSource(text=string_chunk), self.speak_options
            )

            for chunk in response.stream:
                if chunk:
                    yield chunk

    async def generate_audio_stream_from_text(
        self,
        text: str,
    ) -> AsyncGenerator[bytes, None]:
        response = self.deepgram.speak.v("1").stream_memory(
            TextSource(text=text), self.speak_options
        )
        for chunk in response.stream:
            if chunk:
                yield chunk
