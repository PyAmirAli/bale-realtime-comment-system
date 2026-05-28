from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt
from bson import ObjectId
from datetime import datetime

from utils.helpers import admin_keyboard, reply_keyboard, send_bale_message
from websocket.manager import manager
from db.mongo import db
from core.config import settings

router = APIRouter()

users_collection = db.users
comments_collection = db.comments


@router.websocket("/ws/comments/{post_id}")
async def comments_ws(websocket: WebSocket, post_id: str):

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except:
        await websocket.close(code=1008)
        return
    user = await users_collection.find_one({"_id": ObjectId(payload["user_id"])})

    post = await db.posts.find_one({"_id": post_id})

    if not post:
        await websocket.close(code=1008)
        return
    channel_id = post["channel_id"]
    if channel_id in user.get("banned_channels", []):
        await websocket.send_json({
            "event": "error",
            "message": "شما در این کانال بن شده‌اید"
        })
        return



    if not user:
        await websocket.close(code=1008)
        return

    user["_id"] = str(user["_id"])

    await manager.connect(post_id, websocket)

    cursor = comments_collection.find({"post_id": post_id}).sort("created_at", -1).limit(50)

    history = []
    async for comment in cursor:
        user_doc = await users_collection.find_one({"_id": ObjectId(comment["user_id"])})
        if not user_doc:
            continue  

        comment_data = {
            "_id": str(comment["_id"]),
            "post_id": comment["post_id"],
            "text": comment["text"],
            "reply_to": comment.get("reply_to"),
            "created_at": comment["created_at"].isoformat(),
            "user": {
                "id": str(user_doc["_id"]),
                "first_name": user_doc.get("first_name"),
                "last_name": user_doc.get("last_name"),
                "username": user_doc.get("username"),
                "photo": user_doc.get("photo")
            }
        }
        history.append(comment_data)

    history.reverse()

    await websocket.send_json({
        "event": "history",
        "data": history
    })

    try:

        while True:

            data = await websocket.receive_json()
            event = data.get("event")

            if event == "message":
                comment = {
                    "post_id": post_id,
                    "user_id": user["_id"],
                    "text": data.get("text"),
                    "reply_to": data.get("reply_to"),
                    "created_at": datetime.utcnow()
                }

                result = await comments_collection.insert_one(comment)


                post = await db.posts.find_one({"_id": post_id})

                if post:
                    channel = await db.channels.find_one({
                        "_id": post["channel_id"]
                    })

                    if channel and channel.get("owner"):

                        owner_id = channel["owner"]["id"]
                        text = f"""
💬 کامنت جدید دریافت شد

👤 نام: {user.get("first_name") or "-"}
🔗 یوزرنیم: @{user.get("username") or "-"}
🆔 Bale ID: {user.get("bale_id") or "-"}

📝 متن کامنت:
{comment['text']}
"""



                        await send_bale_message(
                            owner_id,
                            text,
                            admin_keyboard(
                                post_id,
                                str(result.inserted_id),
                                user["_id"]
                            )
                        )

                reply_to = comment.get("reply_to")

                if reply_to:

                    replied_comment = await comments_collection.find_one({
                        "_id": ObjectId(reply_to)
                    })

                    if replied_comment:

                        replied_user_id = replied_comment["user_id"]

                        if replied_user_id != user["_id"]:

                            replied_user = await users_collection.find_one({
                                "_id": ObjectId(replied_user_id)
                            })

                            if replied_user and replied_user.get("bale_id"):
                                username = user.get("username") or user.get("first_name")
                                text = f"""
                                💬 به کامنت شما پاسخ داده شد
                                
👤 {user.get("first_name")}
👤 @{username}

📝 پاسخ:
{comment['text']}
                                """

                                await send_bale_message(
                                    replied_user["bale_id"],
                                    text,
                                    reply_keyboard(post_id)
                                )


                payload = {
                    "event": "message",
                    "data": {
                        "_id": str(result.inserted_id),
                        "post_id": post_id,
                        "text": comment["text"],
                        "reply_to": comment["reply_to"],
                        "created_at": comment["created_at"].isoformat(),
                        "user": {
                            "id": user["_id"],
                            "first_name": user.get("first_name"),
                            "last_name": user.get("last_name"),
                            "username": user.get("username"),
                            "photo": user.get("photo")
                        }
                    }
                }

                await manager.broadcast(post_id, payload)




            elif event == "typing":

                payload = {
                    "event": "typing",
                    "user": {
                        "id": user["_id"],
                        "first_name": user.get("first_name"),
                        "photo": user.get("photo")
                    }
                }

                await manager.broadcast(post_id, payload)

    except WebSocketDisconnect:
        manager.disconnect(post_id, websocket)
