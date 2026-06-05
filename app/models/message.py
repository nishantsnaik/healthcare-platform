from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class MessageType(str, Enum):
    SECUREMESSAGE = "secure message"
    BROADCAST = "broadcast"
    TEAMNOTIFICATION = "team notification"

class MessageBase(BaseModel):
    #recipient: str
    sender_id: int
    type: MessageType
    content: str
    recipient_id: Optional[int] = None  # for secure messages
    recipient_unit: Optional[str] = None  # for broadcasts

class CreateMessageBase(MessageBase):
    pass

class MessageUpdate(BaseModel):
    delivered_date_time: Optional[datetime]
    read_date_time: Optional[datetime]


class Message(MessageBase):
    id: int
    delivered_date_time: Optional[datetime]
    sent_date_time: datetime
    read_date_time: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime] = None
