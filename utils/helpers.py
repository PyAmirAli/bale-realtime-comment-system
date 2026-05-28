import os
import httpx
import hmac
import hashlib
import urllib.parse

from core.config import settings


BASE_API = "https://tapi.bale.ai"
BASE_BOT_URL = f"{BASE_API}/bot{settings.TOKEN}"

STORAGE_PATH = "storage"
CHANNEL_PATH = f"{STORAGE_PATH}/channels"
USER_PATH = f"{STORAGE_PATH}/users"

os.makedirs(CHANNEL_PATH, exist_ok=True)
os.makedirs(USER_PATH, exist_ok=True)



async def _get_file_path(client: httpx.AsyncClient, file_id: str):
    res = await client.get(
        f"{BASE_BOT_URL}/getFile",
        params={"file_id": file_id}
    )
    res.raise_for_status()
    return res.json()["result"]["file_path"]


async def _download_file(client: httpx.AsyncClient, file_path: str, local_path: str):

    download_url = f"{BASE_API}/file/bot{settings.TOKEN}/{file_path}"

    img_res = await client.get(download_url)
    img_res.raise_for_status()

    with open(local_path, "wb") as f:
        f.write(img_res.content)

    return local_path




async def get_channel_info(chat_id: str):

    try:

        async with httpx.AsyncClient(timeout=10) as client:

            chat_res = await client.get(
                f"{BASE_BOT_URL}/getChat",
                params={"chat_id": chat_id}
            )
            chat_res.raise_for_status()

            chat_data = chat_res.json()["result"]

            name = chat_data.get("title")
            photo_path = None

            if "photo" in chat_data:

                file_id = (
                    chat_data["photo"].get("big_file_id")
                    or chat_data["photo"].get("small_file_id")
                )

                photo_path = await download_channel_photo(
                    client,
                    chat_id,
                    file_id
                )

            count_res = await client.get(
                f"{BASE_BOT_URL}/getChatMembersCount",
                params={"chat_id": chat_id}
            )

            count_res.raise_for_status()

            members = count_res.json()["result"]

            return {
                "id": chat_id,
                "name": name,
                "members": members,
                "photo": photo_path
            }

    except Exception as e:
        print("Bale API Error:", e)
        return None


async def download_channel_photo(
    client: httpx.AsyncClient,
    chat_id: str,
    file_id: str
):

    file_path_local = f"{CHANNEL_PATH}/{chat_id}.jpg"

    if os.path.exists(file_path_local):
        return f"/storage/channels/{chat_id}.jpg"

    file_path = await _get_file_path(client, file_id)

    await _download_file(client, file_path, file_path_local)

    return f"/storage/channels/{chat_id}.jpg"


async def download_post_photo(
    chat_id: str,
    file_id: str,
    post_id: str = None
):

    if post_id:
        file_path_local = f"{CHANNEL_PATH}/{chat_id}-{post_id}.jpg"
    else:
        file_path_local = f"{CHANNEL_PATH}/{chat_id}.jpg"

    if os.path.exists(file_path_local):
        return file_path_local

    async with httpx.AsyncClient(timeout=10) as client:

        file_path = await _get_file_path(client, file_id)

        await _download_file(client, file_path, file_path_local)

    return file_path_local


async def download_user_photo(
    client: httpx.AsyncClient,
    user_id: int,
    file_id: str
):

    file_path_local = f"{USER_PATH}/{user_id}.jpg"

    if os.path.exists(file_path_local):
        return f"/storage/users/{user_id}.jpg"

    file_path = await _get_file_path(client, file_id)

    await _download_file(client, file_path, file_path_local)

    return f"/storage/users/{user_id}.jpg"

async def get_user_info(user_id: int):

    try:

        async with httpx.AsyncClient(timeout=10) as client:

            photos_res = await client.get(
                f"{BASE_BOT_URL}/getChat",
                params={"chat_id": user_id}
            )



            photos_res.raise_for_status()

            photos_data = photos_res.json()["result"]

            photo_path = None

            if photos_data.get("photo"):

                file_id = photos_data["photo"]["big_file_id"]

                photo_path = await download_user_photo(
                    client,
                    user_id,
                    file_id
                )

            return {
                "id": user_id,
                "photo": photo_path
            }

    except Exception as e:
        print("Bale API Error:", e)
        return None


def verify_bale_init_data(init_data: str):

    parsed = dict(urllib.parse.parse_qsl(init_data))

    received_hash = parsed.pop("hash", None)

    if not received_hash:
        return False

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(
        settings.TOKEN.encode(),
        b"WebAppData",
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(calculated_hash, received_hash)



async def send_bale_message(chat_id: int, text: str, keyboard=None):

    url = f"https://tapi.bale.ai/bot{settings.TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        payload["reply_markup"] = keyboard

    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)


def admin_keyboard(post_id, comment_id, user_id):

    return {
        "inline_keyboard": [
            [
                {
                    "text": "🚫 بن کاربر",
                    "callback_data": f"ban:{user_id}"
                },
                {
                    "text": "🗑 حذف کامنت",
                    "callback_data": f"delete:{comment_id}"
                }
            ],
            [
                {
                    "text": "💬 مشاهده کامنت",
                    "web_app": {
                        "url": f"{settings.WEBAPP_URL}?id={post_id}"
                    }
                }
            ]
        ]
    }


def reply_keyboard(post_id):

    return {
        "inline_keyboard": [
            [
                {
                    "text": "💬 مشاهده پاسخ",
                    "web_app": {
                        "url": f"{settings.WEBAPP_URL}?id={post_id}"
                    }
                }
            ]
        ]
    }
