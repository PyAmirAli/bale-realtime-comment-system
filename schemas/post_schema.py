from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional



class ChannelSchema(BaseModel):
    id: str
    name: Optional[str] = None
    members: Optional[int] = None
    photo: Optional[str] = None


class MessageSchema(BaseModel):
    text: Optional[str] = None
    image: Optional[str] = None
    created_at: Optional[datetime] = None



class PostResponseSchema(BaseModel):
    post_id: str
    channel: ChannelSchema
    message: MessageSchema