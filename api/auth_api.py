from datetime import datetime, timedelta
import urllib.parse
from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
import json
from utils.helpers import *
from jose import jwt
from core.config import settings
from db.collections import users_collection



router = APIRouter()



@router.post("/verify_user")
async def verify_user(request: Request):

    body = await request.json()

    if not body or "initData" not in body:
        return JSONResponse(
            status_code=400,
            content={"error": "فیلد initData الزامی است"}
        )

    init_data = body["initData"]

    # ✅ verify signature
    if not verify_bale_init_data(init_data):
        return JSONResponse(
            status_code=403,
            content={"valid": False, "error": "امضای داده‌ها نامعتبر است"}
        )

    parsed = urllib.parse.parse_qs(init_data)
    user_json = parsed.get("user", ["{}"])[0]

    try:
        user = json.loads(user_json)
    except:
        user = {}

    bale_id = str(user.get("id"))

    if not bale_id:
        return JSONResponse(
            status_code=400,
            content={"error": "شناسه کاربر یافت نشد"}
        )


    db_user = await users_collection.find_one({"bale_id": bale_id})

    if not db_user:


        user_data = await get_user_info(
                bale_id
            )
        photo_path = user_data['photo']

        new_user = {
            "bale_id": bale_id,
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "username": user.get("username"),
            "photo": photo_path,
            "created_at": datetime.utcnow()
        }

        result = await users_collection.insert_one(new_user)

        db_user = {
            "_id": str(result.inserted_id),
            **new_user
        }

    else:
        db_user["_id"] = str(db_user["_id"])



    payload = {
        "user_id": db_user["_id"],
        "bale_id": db_user["bale_id"],
        "exp": datetime.utcnow() + timedelta(days=30)
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm="HS256"
    )

    return {
        "valid": True,
        "token": token,
        "user": {
            "id": db_user["_id"],
            "first_name": db_user.get("first_name"),
            "last_name": db_user.get("last_name"),
            "username": db_user.get("username"),
            "photo": db_user.get("photo")
        }
    }