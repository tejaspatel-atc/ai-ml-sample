import base64
from typing import AsyncIterator, Optional

from app.logger import logger
from app.schema.twilio import MarkEventSchema, MediaEventSchema, TwilioEventSchema
from app.settings import settings
from fastapi.websockets import WebSocket
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import Connect, VoiceResponse


class TwilioCallManager:
    def __init__(self, websocket: Optional[WebSocket] = None) -> None:
        self.client: TwilioClient = TwilioClient(
            username=settings.TWILIO_ACCOUNT_SID,
            password=settings.TWILIO_AUTH_TOKEN,
        )
        self.websocket: WebSocket = websocket
        self.response = VoiceResponse()

    def handle_incoming_call(self, bot_id: str):
        # WebSocket URL for handling audio stream
        connect = Connect()
        connect.stream(
            name=bot_id, url=f"{settings.APP_BACKEND_WEBSOCKET_DOMAIN}/ws/{bot_id}/audio/stream"
        )
        self.response.append(connect)
        self.response.say("Stream Has been Ended.")
        return self.response

    def speak(self, content: str):
        self.response.say(content)

    async def send_chunk(self, stream_sid: str, chunk: bytes) -> None:
        data = TwilioEventSchema(
            event="media",
            streamSid=stream_sid,
            media=MediaEventSchema(
                payload=base64.b64encode(chunk).decode("utf-8"),
            ),
        ).model_dump(exclude_none=True, by_alias=True)
        await self.websocket.send_json(data)

    async def clear_buffer(self, stream_sid: str) -> None:
        data = TwilioEventSchema(
            event="clear",
            streamSid=stream_sid,
        ).model_dump(exclude_none=True, by_alias=True)
        await self.websocket.send_json(data)

    async def send_mark(self, stream_sid: str, mark_name: str) -> None:
        data = TwilioEventSchema(
            event="mark",
            streamSid=stream_sid,
            mark=MarkEventSchema(
                name=mark_name,
            ),
        ).model_dump(exclude_none=True, by_alias=True)
        await self.websocket.send_json(data)
        logger.info(f"AUDIO SENT TO TWILIO - STEAM ID: {stream_sid}")

    async def stream_audio(self, stream_sid: str, audio_stream: AsyncIterator[bytes]) -> None:
        async for chunk in audio_stream:
            await self.send_chunk(
                stream_sid=stream_sid,
                chunk=chunk,
            )
        await self.send_mark(
            stream_sid=stream_sid,
            mark_name=stream_sid,
        )

    async def end_call(self, call_sid: str) -> bool:
        response = self.client.calls(call_sid).update(status="completed")
        return response.status == "completed"  # type: ignore
