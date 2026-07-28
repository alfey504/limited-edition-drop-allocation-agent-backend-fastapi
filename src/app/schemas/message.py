import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.message import MessageRole


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    tool_calls: dict | None
    created_at: datetime
