from fastapi import APIRouter, HTTPException
from db.collections import posts_collection
from utils.helpers import get_channel_info,download_post_photo
from schemas.post_schema import PostResponseSchema
import re
import html


router = APIRouter()


def markdown_v2_to_html(text: str) -> str:
    if not text:
        return ""
    safe_text = html.escape(text)
    safe_text = re.sub(r'\*(.*?)\*', r'<strong>\1</strong>', safe_text, flags=re.DOTALL)
    safe_text = re.sub(r'_(.*?)_', r'<em>\1</em>', safe_text, flags=re.DOTALL)
    safe_text = re.sub(r'@(\w+)', r'<a href="https://t.me/\1" class="text-blue-500">@\1</a>', safe_text)
    safe_text = safe_text.replace('\n', '<br>')
    return safe_text




@router.get("/posts/{post_id}", response_model=PostResponseSchema)
async def get_post(post_id: str):

    post = await posts_collection.find_one({
        "_id": str(post_id)
    })
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    channel_id = post["channel_id"]

    channel = await get_channel_info(channel_id)
    path_image = None
    if post["message"].get("image"):
        id_image = post["message"].get("image")
        path_image = await download_post_photo(channel_id,id_image,post_id)
    return {
        "post_id": str(post["_id"]),
        "channel": {
            "id": channel.get("id"),
            "name": channel.get("name"),
            "members": channel.get("members"),
            "photo": channel.get("photo")
        },
        "message": {
            "text": markdown_v2_to_html(post["message"].get("text")),
            "image": path_image,
            "created_at": post["message"].get("created_at")
        }
    }