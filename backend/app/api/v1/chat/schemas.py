from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    title: str | None = Field(None, max_length=200)
    chat_type: str = Field("general")


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
