from pydantic import BaseModel, Field


class MediaFormatSchema(BaseModel):
    encoding: str
    sample_rate: int = Field(alias="sampleRate")
    channels: int


class StartEventSchema(BaseModel):
    stream_sid: str = Field(alias="streamSid")
    account_sid: str = Field(alias="accountSid")
    call_sid: str = Field(alias="callSid")
    tracks: list[str]
    media_format: MediaFormatSchema = Field(alias="mediaFormat")


class MediaEventSchema(BaseModel):
    track: str | None = None
    chunk: str | None = None
    timestamp: str | None = None
    payload: str


class StopEventSchema(BaseModel):
    account_sid: str = Field(alias="accountSid")
    call_sid: str = Field(alias="callSid")


class MarkEventSchema(BaseModel):
    name: str


class TwilioEventSchema(BaseModel):
    event: str
    sequence_number: str | None = Field(default=None, alias="sequenceNumber")
    stream_sid: str | None = Field(default=None, alias="streamSid")
    start: StartEventSchema | None = None
    media: MediaEventSchema | None = None
    mark: MarkEventSchema | None = None
    stop: StopEventSchema | None = None
