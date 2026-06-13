"""
Message Data Models

This module defines Pydantic models for secure messaging in the healthcare system.
Messages allow caregivers to communicate about patients and clinical situations.

Message types:
- Secure message: Direct message from one caregiver to another
- Broadcast: Message sent to all caregivers in a unit
- Team notification: System-generated notifications to care teams

Model inheritance pattern:
- Base: Common fields for all message models
- Create: Fields needed when creating a new message
- Update: Fields that can be modified (delivery/read status)
- Response: All fields including database-generated ones

For beginners: These models define how caregivers communicate through
the system with different types of messages.
"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class MessageType(str, Enum):
    """
    Enumeration of message types in the healthcare system.
    
    Different message types serve different communication needs:
    - Direct communication between caregivers
    - Broadcasting to entire units
    - System notifications to care teams
    
    Values:
        SECUREMESSAGE: Direct message from one caregiver to another
        BROADCAST: Message sent to all caregivers in a specific unit
        TEAMNOTIFICATION: System-generated notification to a care team
    """
    SECUREMESSAGE = "secure message"
    BROADCAST = "broadcast"
    TEAMNOTIFICATION = "team notification"


class MessageBase(BaseModel):
    """
    Base model containing common message fields.
    
    This is the parent class that other message models inherit from.
    It contains fields that are shared across all message operations.
    
    Attributes:
        sender_id: Unique identifier of the caregiver sending the message
        type: Type of message (from MessageType enum)
        content: The message text content
        recipient_id: ID of specific recipient (for secure messages, optional)
        recipient_unit: Unit to broadcast to (for broadcasts, optional)
    """
    sender_id: int
    type: MessageType
    content: str
    recipient_id: Optional[int] = None  # Used for secure messages
    recipient_unit: Optional[str] = None  # Used for broadcasts


class CreateMessageBase(MessageBase):
    """
    Model for creating a new message.
    
    This model is used when a client sends a POST request to create a message.
    It inherits all fields from MessageBase.
    """
    pass


class MessageUpdate(BaseModel):
    """
    Model for updating an existing message.
    
    This model is used when a client sends a PATCH request to modify a message.
    Typically used to update delivery and read status.
    
    Attributes:
        delivered_date_time: When the message was delivered
        read_date_time: When the message was read by the recipient
    """
    delivered_date_time: Optional[datetime]
    read_date_time: Optional[datetime]


class Message(MessageBase):
    """
    Complete message model including database-generated fields.
    
    This model represents a message as stored in the database, including
    fields that are automatically generated like timestamps.
    
    Additional attributes beyond MessageBase:
        id: Database-generated unique identifier
        delivered_date_time: When the message was delivered
        sent_date_time: When the message was sent
        read_date_time: When the message was read
        created_at: When the message record was created
        updated_at: When the message record was last modified
    """
    id: int
    delivered_date_time: Optional[datetime]
    sent_date_time: datetime
    read_date_time: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime] = None
