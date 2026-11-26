from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional


class UserCreate(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    email: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ConversationCreate(BaseModel):
    title: Optional[str] = "New conversation"


class MessageCreate(BaseModel):
    content: str


class MessageRead(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationRead(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: List[MessageRead] = []
    model_config = ConfigDict(from_attributes=True)


class MessageExchange(BaseModel):
    user_message: MessageRead
    assistant_message: MessageRead
    cached: bool = False
