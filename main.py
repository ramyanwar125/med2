import os, asyncio, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from engine import get_all_formats, run_download

# --- إعدادات البيئة ---
CONFIG = {
    "API_ID": 33536164,
    "API_HASH": "c4f81cfa1dc011bcf66c6a4a58560fd2",
    "BOT_TOKEN": "8416461275:AAEa8gbeIbSLSCIWOlCSG8IHYl0kiAkDLps",
    "ADMIN_ID": 7349033289,
    "DEV_USER": "@TOP_1UP",
    "BOT_NAME": "『 ＦＡＳＴ ＭＥＤＩＡ 』",
    "CHANNEL_USER": "Fast_Mediia",
    "USERS_FILE": "users_database.txt"
}

app = Client("fast_media_v8069", api_id=CONFIG["API_ID"], api_hash=CONFIG["API_HASH"], bot_token=CONFIG["BOT_TOKEN"])
user_cache = {}

# --- السيرفر الوهمي (Render) ---
def run_health_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Running")
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), Handler).serve_forever()

# --- الوظائف المساعدة ---
def manage_user(user_id):
    if not os.path.exists(CONFIG["USERS_FILE"]): open(CONFIG["USERS_FILE"], "w").close()
    users = open(CONFIG["USERS_FILE"], "r").read().splitlines()
    if str(user_id) not in users:
        with open(CONFIG["USERS_FILE"], "a") as f: f.write(f"{user_id}\n")
    return len(users)

async def check_sub(client, message):
    try:
        await client.get_chat_member(CONFIG["CHANNEL_USER"], message.from_user.id)
        return True
    except:
        btn = [[InlineKeyboardButton("✅ اشترك هنا", url=f"https://t.me/{CONFIG['CHANNEL_USER']}")]]
        await message.reply("⚠️ اشترك أولاً ثم أرسل /start", reply_markup=InlineKeyboardMarkup(btn))
        return False

# --- معالجة الأوامر ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if not await check_sub(client, message): return
    manage_user(message.from_user.id)
    kb = [['🔄 Restart Service | بدء الخدمة'], ['👨‍💻 Developer | المطور']]
    if message.from_user.id == CONFIG["ADMIN_ID"]: kb.append(['📣 Broadcast | إذاعة'])
    await message.reply(f"✨ أهلاً بك في {CONFIG['BOT_NAME']}\nأرسل الرابط الآن!", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

@app.on_message(filters.text & filters.private)
async def handle_text(client, message):
    if not await check_sub(client, message): return
    text, user_id = message.text, message.from_user.id
    
    if "http" in text:
        status = await message.reply("🔍 جاري المعالجة...")
        try:
            formats = await asyncio.to_thread(get_all_formats, text)
            user_cache[user_id] = text
            btns = [[InlineKeyboardButton(res, callback_data=fid)] for res, fid in formats.items()]
            await status.edit("✅ اختر الجودة:", reply_markup=InlineKeyboardMarkup(btns))
        except: await status.edit("❌ خطأ في المعالجة")
    # (يمكنك إضافة منطق الإذاعة والمطور هنا بنفس النمط)

@app.on_callback_query()
async def download_cb(client, callback_query):
    f_id, user_id = callback_query.data, callback_query.from_user.id
    url = user_cache.get(user_id)
    if not url: return await callback_query.answer("⚠️ انتهت الجلسة")
    
    await callback_query.message.edit("⚙️ جاري التحميل...")
    ext = 'm4a' if "audio" in f_id else 'mp4'
    path = f"media_{user_id}.{ext}"
    
    try:
        await asyncio.to_thread(run_download, url, f_id, path)
        if os.path.exists(path):
            send_func = client.send_audio if ext == 'm4a' else client.send_video
            await send_func(user_id, path, caption=f"🎬 Done by {CONFIG['BOT_NAME']}")
            await callback_query.message.delete()
    finally:
        if os.path.exists(path): os.remove(path)

# --- الحل الجذري لمشكلة الـ Event Loop ---
async def main():
    # تشغيل السيرفر في خلفية الخيط الرئيسي
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # تشغيل البوت باستخدام context manager لضمان استقرار الحلقة
    async with app:
        print("🚀 البوت يعمل الآن بنجاح على Render!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        # هذه الدالة هي الطريقة الصحيحة لتشغيل asyncio في بايثون الحديثة
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
