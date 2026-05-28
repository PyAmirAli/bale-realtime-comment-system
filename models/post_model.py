from pydantic import BaseModel
from typing import Optional


class ChannelModel(BaseModel):
    id: str
    name: str
    username: Optional[str] = None
    avatar: Optional[str] = None
    members_count: int


class MessageModel(BaseModel):
    text: str
    image: Optional[str] = None
    created_at: str


class PostModel(BaseModel):
    id: str
    channel: ChannelModel
    message: MessageModel
    bale_message_id: str
