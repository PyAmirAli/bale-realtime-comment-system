# 🚀 Bale Real-Time Comment System | سیستم دیدگاه برای بله

A real-time comment system designed to bring interactive discussions to Bale messenger posts.
سیستم کامنت‌گذاری لحظه‌ای برای اضافه کردن قابلیت دیدگاه به پست‌های بله

---

## ✨ Features | امکانات

* ⚡ Real-time messaging (WebSocket)
  چت لحظه‌ای با وب‌سوکت
* 💬 Comment system for posts
  سیستم کامنت برای پست‌ها
* 🔁 Reply to messages
  پاسخ به پیام‌ها
* ❤️ Reactions
  امکان ری‌اکشن
* ⌨️ Typing indicator
  نمایش در حال تایپ
* 🌐 Web-based UI (Tailwind)
  رابط کاربری تحت وب

---

## 🧠 How It Works | نحوه کار

1. User sends a post in Bale
   کاربر پست را در بله ارسال می‌کند
2. Bot edits the post and adds a "View Comments" button
   ربات پست را ادیت کرده و دکمه «دیدگاه» اضافه می‌کند
3. User clicks and opens web app
   کاربر وارد وب‌اپ می‌شود
4. Real-time discussion starts
   گفتگو به صورت لحظه‌ای شروع می‌شود

---

## 🏗️ Project Structure | ساختار پروژه

```
.
├── api/            # API routes
├── core/           # Config & settings
├── db/             # MongoDB connection & collections
├── models/         # Data models
├── schemas/        # Pydantic schemas
├── websocket/      # WebSocket logic
├── templates/      # HTML صفحات
├── storage/        # فایل‌های آپلودی
├── utils/          # ابزارهای کمکی
├── bot.py          # ربات بله
├── main.py         # ورودی FastAPI
```

---

## ⚙️ Tech Stack | تکنولوژی‌ها

* **FastAPI**
* **WebSockets**
* **MongoDB**
* **Tailwind CSS**
* **Bale Bot API**

---

## ⚙️ Installation | نصب

```bash
git clone https://github.com/your-username/bale-realtime-comment-system.git
cd bale-realtime-comment-system

pip install -r requirements.txt

uvicorn main:app --reload
```

---

## 🔌 Environment Variables | متغیرهای محیطی

Create `.env` file:

```
MONGO_URL=
DATABASE_NAME=comments
TOKEN=
JWT_SECRET=f6b402c8d71406aaf0c17548cfd2560458d4e7d8f3a7ded38543ca4ce7aa68f6
WEBAPP_URL=https://google.com
```



## 🚧 Future Improvements | برنامه‌های آینده

* Authentication system
  سیستم احراز هویت
* Admin panel
  پنل مدیریت
* Anti-spam system
  جلوگیری از اسپم
* Multi-platform support
  پشتیبانی از پلتفرم‌های دیگر

---

## 💡 Motivation | هدف پروژه

Bale messenger does not support comments on posts.
This project solves that limitation using a real-time web-based system.

بله به صورت پیش‌فرض سیستم دیدگاه ندارد
این پروژه برای حل این مشکل ساخته شده است

---

## 🤝 Contributing

Pull requests are welcome

---

## ⭐ Support

If you like this project, give it a star ⭐
اگر پروژه را دوست داشتید ستاره بدهید ⭐
