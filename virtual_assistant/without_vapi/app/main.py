import base64
from typing import Annotated, Optional

from app.logger import logger
from app.schema.twilio import MediaFormatSchema, StartEventSchema, TwilioEventSchema
from app.services.conversation import ConversationManager
from app.services.supabase import fetch_bot_details
from app.services.twilio import TwilioCallManager
from fastapi import Depends, FastAPI, Response
from fastapi.websockets import WebSocket, WebSocketDisconnect, WebSocketState

app = FastAPI()

connections: dict[str, StartEventSchema] = {}


@app.websocket("/ws/{bot_id}/audio/stream")
async def websocket_endpoint(websocket: WebSocket, bot_id: str):
    # Fetch bot details from Supabase on connection initialization
    bot_data = fetch_bot_details(bot_id)
    if not bot_data:
        return None
    await websocket.accept()
    conversation_manager: Optional[ConversationManager] = None
    try:
        while True:
            # Receive data from WebSocket (user's words from Twilio)
            packet = await websocket.receive_text()

            if packet is None:
                continue

            validated_packet = TwilioEventSchema.model_validate_json(packet)

            match validated_packet.event:
                case "connected":
                    logger.info("A NEW CALL HAS CONNECTED")
                case "start":
                    conversation_manager = ConversationManager(
                        bot_id=bot_id,
                        websocket=websocket,
                        bot_details=bot_data,
                        call_sid=validated_packet.start.call_sid,
                        stream_sid=validated_packet.start.stream_sid,
                    )
                    if validated_packet.start:
                        call_sid = validated_packet.start.call_sid
                        connections[call_sid] = StartEventSchema(
                            streamSid=validated_packet.start.stream_sid,
                            accountSid=validated_packet.start.account_sid,
                            callSid=validated_packet.start.call_sid,
                            tracks=validated_packet.start.tracks,
                            mediaFormat=MediaFormatSchema(
                                encoding=validated_packet.start.media_format.encoding,
                                channels=validated_packet.start.media_format.channels,
                                sampleRate=validated_packet.start.media_format.sample_rate,
                            ),
                        )
                        logger.info(
                            "STARTED MEDIA STREAM - " f"STREAM ID: {validated_packet.stream_sid}"
                        )
                        if not await conversation_manager._is_bot_available():
                            await conversation_manager._end_call(
                                "This bot is out of service for now."
                            )
                        await conversation_manager.start()
                case "media":
                    if validated_packet.media and conversation_manager:
                        chunk = base64.b64decode(validated_packet.media.payload)
                        await conversation_manager.receive_audio(chunk)
                case "stop":
                    if call_sid:
                        logger.info(
                            "CALL HAS ENDED - STREAM ID: " f"{connections[call_sid].stream_sid}"
                        )
                    break

    except WebSocketDisconnect as e:
        logger.error(
            "WebSocketDisconnect Error Occurred: %s; at line no: %s",
            str(e),
            str(e.__traceback__.tb_lineno),
        )
    except Exception as e:
        logger.error("Error Occurred: %s; at line no: %s", str(e), str(e.__traceback__.tb_lineno))
    finally:
        if call_sid and call_sid in connections:
            connections.pop(call_sid)
        if conversation_manager and conversation_manager.is_active.is_set():
            await conversation_manager.stop()
        if not WebSocketState.DISCONNECTED:
            await websocket.close()


@app.post("/call/inbound/receive/{bot_id}")
async def inbound_call_receiver(
    bot_id: str,
    twilio_call_manager=Annotated[TwilioCallManager, Depends(TwilioCallManager)],
):
    twilio_call_manager: TwilioCallManager = twilio_call_manager()
    response = twilio_call_manager.handle_incoming_call(bot_id)
    return Response(content=str(response), media_type="application/xml")
