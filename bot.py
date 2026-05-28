import asyncio
from balethon.enums import ChatType
from balethon import Client
from balethon.objects import InlineKeyboard, InlineKeyboardButton
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

bot = Client("")
mongo = AsyncIOMotorClient("mongodb://localhost:27017")
db = mongo.comments
comments = db.comments
posts = db.posts
channels = db.channels
users = db.users

WEBAPP_BASE = "https://google.com"


async def is_owner_of_channel(user_id: int, channel_id: str) -> bool:
    ch = await channels.find_one({"_id": channel_id, "owner.id": user_id})
    return ch is not None


@bot.on_message()
async def handle_message(message):
    chat_type = message.chat.type

    if chat_type == ChatType.PRIVATE:
        state = message.author.get_state()

        if state and state.startswith("SET_BUTTON:"):
            channel_id = state.split(":")[1]
            await channels.update_one(
                {"_id": channel_id},
                {"$set": {"button_text": message.text}}
            )
            message.author.del_state()
            return await message.reply("✅ متن دکمه ذخیره شد.")

        if state and state.startswith("SEARCH_USER:"):
            channel_id = state.split(":")[1]
            query = message.text.strip()
            user_doc = None
            if query.isdigit():
                user_doc = await users.find_one({"telegram_id": int(query)})
            else:
                username = query.lstrip("@")
                user_doc = await users.find_one({"username": username})

            if user_doc:
                name_parts = []
                if user_doc.get("first_name"):
                    name_parts.append(user_doc["first_name"])
                if user_doc.get("last_name"):
                    name_parts.append(user_doc["last_name"])
                full_name = " ".join(name_parts) if name_parts else "بی‌نام"
                tg_id = user_doc.get("telegram_id", "نامشخص")
                username = user_doc.get("username", "ندارد")
                banned_channels = user_doc.get("banned_channels", [])
                is_banned = channel_id in banned_channels
                ban_status = "🚫 بن شده" if is_banned else "✅ آزاد"

                text = (
                    f"👤 <b>{full_name}</b>\n"
                    f"🆔 شناسه: <code>{tg_id}</code>\n"
                    f"🔗 یوزرنیم: @{username}\n"
                    f"🚫 وضعیت در این کانال: {ban_status}"
                )

                if is_banned:
                    keyboard = InlineKeyboard(
                        [("✅ آنبن کردن", f"unban:{user_doc['_id']}:{channel_id}")],
                        [("🔙 بازگشت", f"panel:{channel_id}")]
                    )
                else:
                    keyboard = InlineKeyboard(
                        [("🚫 بن کردن", f"ban:{user_doc['_id']}:{channel_id}")],
                        [("🔙 بازگشت", f"panel:{channel_id}")]
                    )

                message.author.del_state()
                return await message.reply(text, reply_markup=keyboard)
            else:
                return await message.reply("❌ کاربری با این مشخصات یافت نشد. می‌توانید دوباره امتحان کنید یا /start را بزنید.")

        if message.text != "/start":
            return

        user_id = message.author.id
        user_channels_cursor = channels.find({"owner.id": user_id})
        user_channels_list = await user_channels_cursor.to_list(None)
        channel_count = len(user_channels_list)
        channel_ids = [ch["_id"] for ch in user_channels_list]

        post_count = 0
        comment_count = 0
        if channel_ids:
            post_count = await posts.count_documents({"channel_id": {"$in": channel_ids}})
            post_ids_cursor = posts.find({"channel_id": {"$in": channel_ids}}, {"_id": 1})
            post_ids = [p["_id"] async for p in post_ids_cursor]
            if post_ids:
                comment_count = await comments.count_documents({"post_id": {"$in": post_ids}})

        stats = (
            f"📊 <b>آمار کلی شما:</b>\n"
            f"🔹 تعداد کانال‌ها: {channel_count}\n"
            f"🔹 تعداد پست‌ها: {post_count}\n"
            f"🔹 تعداد کامنت‌ها: {comment_count}\n\n"
            f"📋 یک کانال را برای مدیریت انتخاب کنید:"
        )

        if not user_channels_list:
            return await message.reply("ℹ️ شما هنوز هیچ کانالی را به ربات اضافه نکرده‌اید.")

        buttons = []
        for ch in user_channels_list:
            buttons.append((ch["title"], f"panel:{ch['_id']}"))
        return await message.reply(
            stats,
            reply_markup=InlineKeyboard(buttons),
            
        )

    if chat_type == ChatType.CHANNEL:
        channel_id = str(message.chat.id)
        post_id = str(message.id)

        channel = await channels.find_one({"_id": channel_id})
        if not channel:
            chat = await bot.get_chat(channel_id)
            admins = await bot.get_chat_administrators(channel_id)
            owner = None
            for admin in admins:
                if admin.status == "creator":
                    owner = {
                        "id": admin.user.id,
                        "name": admin.user.first_name,
                        "username": admin.user.username
                    }
                    break
            await channels.insert_one({
                "_id": channel_id,
                "title": chat.title,
                "username": chat.username,
                "owner": owner,
                "comments_enabled": True,
                "button_text": "💬 دیدگاه‌ها"
            })
            confirm = await bot.send_message(
                channel_id,
                "✅ ربات با موفقیت فعال شد.\nاین پیام به‌زودی حذف می‌شود."
            )
            await asyncio.sleep(5)
            await confirm.delete()
            channel = await channels.find_one({"_id": channel_id})

        if not channel.get("comments_enabled", True):
            return

        image_ids = None
        text = message.caption or message.text
        if message.photo:
            image_ids = [p.id for p in message.photo]

        await posts.update_one(
            {"_id": post_id},
            {"$set": {
                "channel_id": channel_id,
                "message": {
                    "text": text,
                    "image": image_ids,
                    "created_at": message.date
                }
            }},
            upsert=True
        )

        button_text = channel.get("button_text", "💬 دیدگاه‌ها")
        webapp_url = f"{WEBAPP_BASE}/?id={post_id}"
        keyboard = InlineKeyboard([
            InlineKeyboardButton(button_text, web_app=webapp_url)
        ])

        try:
            await message.edit(text=text, reply_markup=keyboard)
        except Exception:
            pass


@bot.on_edited_message()
async def handle_edit(message_edit):
    if message_edit.chat.type != "channel":
        return

    post_id = str(message_edit.id)
    image_ids = None
    text = message_edit.caption or message_edit.text
    if message_edit.photo:
        image_ids = [p.id for p in message_edit.photo]

    await posts.update_one(
        {"_id": post_id},
        {"$set": {
            "message.text": text,
            "message.image": image_ids,
            "message.updated_at": message_edit.edit_date
        }}
    )

    channel = await channels.find_one({"_id": str(message_edit.chat.id)})
    if not channel or not channel.get("comments_enabled", True):
        return

    button_text = channel.get("button_text", "💬 دیدگاه‌ها")
    webapp_url = f"{WEBAPP_BASE}/?id={post_id}"
    keyboard = InlineKeyboard([
            InlineKeyboardButton(button_text, web_app=webapp_url)
        ])
    try:
        await message_edit.edit(text=text, reply_markup=keyboard)
    except Exception:
        pass


@bot.on_callback_query()
async def handle_callbacks(callback_query):
    data = callback_query.data
    author_id = callback_query.author.id

    if data == "channels_list":
        user_channels_cursor = channels.find({"owner.id": author_id})
        user_channels_list = await user_channels_cursor.to_list(None)
        if not user_channels_list:
            return await callback_query.message.edit("ℹ️ شما کانالی ندارید.")
        channel_count = len(user_channels_list)
        channel_ids = [ch["_id"] for ch in user_channels_list]
        post_count = await posts.count_documents({"channel_id": {"$in": channel_ids}})
        post_ids_cursor = posts.find({"channel_id": {"$in": channel_ids}}, {"_id": 1})
        post_ids = [p["_id"] async for p in post_ids_cursor]
        comment_count = await comments.count_documents({"post_id": {"$in": post_ids}}) if post_ids else 0

        stats = (
            f"📊 <b>آمار کلی شما:</b>\n"
            f"🔹 تعداد کانال‌ها: {channel_count}\n"
            f"🔹 تعداد پست‌ها: {post_count}\n"
            f"🔹 تعداد کامنت‌ها: {comment_count}\n\n"
            f"📋 یک کانال را برای مدیریت انتخاب کنید:"
        )
        buttons = [(ch["title"], f"panel:{ch['_id']}") for ch in user_channels_list]
        return await callback_query.message.edit(
            stats,
            reply_markup=InlineKeyboard(buttons),
            
        )

    if data.startswith("panel:"):
        channel_id = data.split(":")[1]
        ch = await channels.find_one({"_id": channel_id})
        if not ch:
            return await callback_query.answer("❌ کانال یافت نشد.", show_alert=True)

        status_text = "🟢 روشن" if ch.get("comments_enabled", True) else "🔴 خاموش"
        keyboard = InlineKeyboard(
            [(f"💬 کامنت‌ها: {status_text}", f"toggle:{channel_id}")],
            [("✏️ تغییر متن دکمه", f"text:{channel_id}")],
            [("🔍 جستجوی کاربر", f"search:{channel_id}")],
            [("🔙 بازگشت به لیست کانال‌ها", "channels_list")]
        )
        return await callback_query.message.edit(
            f"⚙️ تنظیمات کانال {ch.get('title', '')}",
            reply_markup=keyboard
        )

    if data.startswith("toggle:"):
        channel_id = data.split(":")[1]
        ch = await channels.find_one({"_id": channel_id})
        if not ch:
            return await callback_query.answer("❌ کانال یافت نشد.", show_alert=True)

        new_status = not ch.get("comments_enabled", True)
        await channels.update_one(
            {"_id": channel_id},
            {"$set": {"comments_enabled": new_status}}
        )
        status_text = "🟢 روشن" if new_status else "🔴 خاموش"
        keyboard = InlineKeyboard(
            [(f"💬 کامنت‌ها: {status_text}", f"toggle:{channel_id}")],
            [("✏️ تغییر متن دکمه", f"text:{channel_id}")],
            [("🔍 جستجوی کاربر", f"search:{channel_id}")],
            [("🔙 بازگشت به لیست کانال‌ها", "channels_list")]
        )
        return await callback_query.message.edit(
            f"⚙️ تنظیمات کانال {ch.get('title', '')}",
            reply_markup=keyboard
        )

    if data.startswith("text:"):
        channel_id = data.split(":")[1]
        callback_query.author.set_state(f"SET_BUTTON:{channel_id}")
        return await callback_query.message.edit(
            "✏️ لطفاً متن جدید دکمه را ارسال کنید.",
            reply_markup=InlineKeyboard([("🔙 بازگشت", f"panel:{channel_id}")])
        )

    if data.startswith("search:"):
        channel_id = data.split(":")[1]
        callback_query.author.set_state(f"SEARCH_USER:{channel_id}")
        return await callback_query.message.edit(
            "🔍 لطفاً <b>شناسه عددی</b> (Telegram ID) یا <b>نام کاربری</b> کاربر را ارسال کنید:",
            
            reply_markup=InlineKeyboard([("🔙 بازگشت", f"panel:{channel_id}")])
        )

    if data.startswith("ban:") or data.startswith("unban:"):
        parts = data.split(":")
        if len(parts) != 3:
            return await callback_query.answer("❌ داده نامعتبر.", show_alert=True)

        action = parts[0] 
        user_id_str = parts[1]
        channel_id = parts[2]

        if not await is_owner_of_channel(author_id, channel_id):
            return await callback_query.answer("⛔ شما مالک این کانال نیستید.", show_alert=True)

        user_doc = await users.find_one({"_id": ObjectId(user_id_str)})
        if not user_doc:
            return await callback_query.answer("❌ کاربر یافت نشد.", show_alert=True)

        if action == "ban":
            await users.update_one(
                {"_id": ObjectId(user_id_str)},
                {"$addToSet": {"banned_channels": channel_id}}
            )
            alert_text = f"🚫 کاربر در این کانال بن شد."
            new_ban_status = True
        else:
            await users.update_one(
                {"_id": ObjectId(user_id_str)},
                {"$pull": {"banned_channels": channel_id}}
            )
            alert_text = f"✅ کاربر از بن در این کانال خارج شد."
            new_ban_status = False

        name_parts = []
        if user_doc.get("first_name"):
            name_parts.append(user_doc["first_name"])
        if user_doc.get("last_name"):
            name_parts.append(user_doc["last_name"])
        full_name = " ".join(name_parts) if name_parts else "بی‌نام"
        tg_id = user_doc.get("telegram_id", "نامشخص")
        username = user_doc.get("username", "ندارد")
        status_text = "🚫 بن شده" if new_ban_status else "✅ آزاد"

        new_text = (
            f"👤 <b>{full_name}</b>\n"
            f"🆔 شناسه: <code>{tg_id}</code>\n"
            f"🔗 یوزرنیم: @{username}\n"
            f"🚫 وضعیت در این کانال: <b>{status_text}</b>"
        )

        if new_ban_status:
            keyboard = InlineKeyboard(
                [("✅ آنبن کردن", f"unban:{user_id_str}:{channel_id}")],
                [("🔙 بازگشت", f"panel:{channel_id}")]
            )
        else:
            keyboard = InlineKeyboard(
                [("🚫 بن کردن", f"ban:{user_id_str}:{channel_id}")],
                [("🔙 بازگشت", f"panel:{channel_id}")]
            )

        await callback_query.answer(alert_text, show_alert=True)
        return await callback_query.message.edit(new_text, reply_markup=keyboard)

    if data.startswith("delete:"):
        comment_id = data.split(":")[1]
        comment = await comments.find_one({"_id": ObjectId(comment_id)})
        if not comment:
            return await callback_query.answer("🗑 کامنت قبلاً حذف شده است.", show_alert=True)

        post = await posts.find_one({"_id": comment.get("post_id")})
        if not post:
            return await callback_query.answer("❌ پست مربوطه یافت نشد.", show_alert=True)

        channel_id = post.get("channel_id")
        if not await is_owner_of_channel(author_id, channel_id):
            return await callback_query.answer("⛔ شما مالک این کانال نیستید.", show_alert=True)

        comment_user = await users.find_one({"_id": comment.get("user_id")})
        user_name = "کاربر ناشناس"
        if comment_user:
            parts = []
            if comment_user.get("first_name"):
                parts.append(comment_user["first_name"])
            if comment_user.get("last_name"):
                parts.append(comment_user["last_name"])
            user_name = " ".join(parts) if parts else "بی‌نام"

        await comments.delete_one({"_id": ObjectId(comment_id)})
        await callback_query.answer("🗑 کامنت حذف شد.", show_alert=True)

        deleted_text = (
            f"🗑 <b>کامنت حذف شد</b>\n"
            f"👤 نویسنده: {user_name}\n"
            f"💬 متن: {comment.get('text', '')[:100]}"
        )
        keyboard = InlineKeyboard([
            ("🔙 بازگشت", f"panel:{channel_id}")
        ])
        return await callback_query.message.edit(deleted_text, reply_markup=keyboard)

    await callback_query.answer("عملیات نامشخص", show_alert=True)


bot.run()