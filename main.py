import os, asyncio, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from engine import get_all_formats, run_download

# --- Web Server for Render | خادم ويب لإرضاء منصة ريندر ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Alive!")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- Config | الإعدادات ---
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

# --- Functions | الوظائف ---
def manage_user(user_id, mode="add"):
    if not os.path.exists(CONFIG["USERS_FILE"]): open(CONFIG["USERS_FILE"], "w").close()
    users = open(CONFIG["USERS_FILE"], "r").read().splitlines()
    if mode == "add" and str(user_id) not in users:
        with open(CONFIG["USERS_FILE"], "a") as f: f.write(f"{user_id}\n")
    return len(users)

async def check_subscription(client, message):
    try:
        await client.get_chat_member(CONFIG["CHANNEL_USER"], message.from_user.id)
        return True
    except UserNotParticipant:
        await message.reply(
            f"⚠️ **عذراً، يجب عليك الاشتراك في القناة أولاً!**\n\nقناة البوت: @{CONFIG['CHANNEL_USER']}\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Join Channel | اشترك الآن", url=f"https://t.me/{CONFIG['CHANNEL_USER']}") ]])
        )
        return False
    except: return True

async def progress_bar(current, total, status_msg, start_time):
    diff = time.time() - start_time
    if diff < 2.5: return
    perc = current * 100 / total
    bar = "▬" * int(perc // 10) + "▭" * (10 - int(perc // 10))
    tmp = (f"🚀 **Transferring.. جاري النقل**\n━━━━━━━━━━━━━━━━━━\n\n"
           f"◈ **Progress:** `{bar}` **{perc:.1f}%**\n"
           f"◈ **Speed:** `{current/diff/(1024*1024):.2f} MB/s` ⚡️\n━━━━━━━━━━━━━━━━━━")
    try: await status_msg.edit(tmp)
    except: pass

# --- Handlers | الأوامر ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if not await check_subscription(client, message): return
    manage_user(message.from_user.id)
    kb = [['🔄 Restart Service | بدء الخدمة'], ['👨‍💻 Developer | المطور']]
    if message.from_user.id == CONFIG["ADMIN_ID"]: kb.append(['📣 Broadcast | إذاعة'])
    
    welcome = (f"✨━━━━━━━━━━━━━✨\n  🙋‍♂️ Welcome **{message.from_user.first_name}**\n"
               f"  🌟 In **{CONFIG['BOT_NAME']}** World\n✨━━━━━━━━━━━━━✨\n\n"
               f"🚀 **Fast Downloader for:**\n📹 YouTube | 📸 Instagram | 🎵 TikTok\n\n👇 **Send link now!**")
    await message.reply(welcome, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

@app.on_message(filters.text & filters.private)
async def handle_text(client, message):
    if not await check_subscription(client, message): return
    text, user_id = message.text, message.from_user.id
    
    if text == '🔄 Restart Service | بدء الخدمة':
        return await message.reply("📡 **System Ready.. النظام جاهز!** ⚡️")
    
    if text == '👨‍💻 Developer | المطور':
        msg = f"👑 **Main Dev:** {CONFIG['DEV_USER']}\n📢 **Channel:** @{CONFIG['CHANNEL_USER']}\n"
        if user_id == CONFIG["ADMIN_ID"]: msg += f"📊 **Total Users:** `{manage_user(user_id, 'count')}`"
        return await message.reply(msg)

    if text == '📣 Broadcast | إذاعة' and user_id == CONFIG["ADMIN_ID"]:
        user_cache[f"bc_{user_id}"] = True
        return await message.reply("📥 **Send your message:**")

    if user_cache.get(f"bc_{user_id}"):
        users = open(CONFIG["USERS_FILE"]).read().splitlines()
        for u in users:
            try: await message.copy(int(u))
            except: pass
        user_cache[f"bc_{user_id}"] = False
        return await message.reply("✅ **Broadcast Sent**")

    if "http" in text:
        status = await message.reply("🔍 **Analyzing.. جاري المعالجة** ⏳")
        try:
            formats = await asyncio.to_thread(get_all_formats, text)
            user_cache[user_id] = text
            btns = [[InlineKeyboardButton(res, callback_data=fid)] for res, fid in formats.items()]
            await status.edit("✅ **Formats Found**", reply_markup=InlineKeyboardMarkup(btns))
        except: await status.edit("❌ **Error | فشل المعالجة**")

@app.on_callback_query()
async def download_cb(client, callback_query):
    f_id, user_id = callback_query.data, callback_query.from_user.id
    url = user_cache.get(user_id)
    if not url: return await callback_query.answer("⚠️ Session Expired", show_alert=True)
    
    await callback_query.message.edit("⚙️ **Processing.. جاري التنفيذ**")
    ext = 'm4a' if "audio" in f_id else 'mp4'
    file_path = f"media_{user_id}.{ext}"
    
    try:
        await asyncio.to_thread(run_download, url, f_id, file_path)
        if os.path.exists(file_path):
            st = time.time()
            send_func = client.send_audio if ext == 'm4a' else client.send_video
            await send_func(user_id, file_path, caption=f"🎬 **By {CONFIG['BOT_NAME']}**", progress=progress_bar, progress_args=(callback_query.message, st))
            
            thanks = (f"✨ **Mission Completed** ✨\n━━━━━━━━━━━━━━━━━━\n🤖 **Bot:** `{CONFIG['BOT_NAME']}`\n"
                      f"👨‍💻 **Dev:** {CONFIG['DEV_USER']}\n📢 **Channel:** @{CONFIG['CHANNEL_USER']}\n━━━━━━━━━━━━━━━━━━")
            await client.send_message(user_id, thanks)
            await callback_query.message.delete()
    except Exception as e: await callback_query.message.edit(f"❌ **Failed:** {e}")
    finally:
        if os.path.exists(file_path): os.remove(file_path)

# --- نظام التشغيل المتوافق مع بايثون 3.11+ ---
async def main():
    # تشغيل سيرفر ريندر
    threading.Thread(target=run_health_server, daemon=True).start()
    # تشغيل البوت
    async with app:
        print("✅ Bot is online and running...")
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    users = open(USERS_FILE, "r").read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f: f.write(f"{user_id}\n")

def get_users_count():
    if not os.path.exists(USERS_FILE): return 0
    return len(open(USERS_FILE, "r").read().splitlines())

async def check_subscription(client, message):
    try:
        await client.get_chat_member(CHANNEL_USER, message.from_user.id)
        return True
    except UserNotParticipant:
        await message.reply(
            f"⚠️ **عذراً، يجب عليك الاشتراك في القناة أولاً!**\n\n"
            f"قناة البوت: @{CHANNEL_USER}\n"
            f"بعد الاشتراك، أرسل /start مجدداً.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Join Channel | اشترك الآن", url=f"https://t.me/{CHANNEL_USER}")
            ]])
        )
        return False
    except Exception: return True

async def progress_bar(current, total, status_msg, start_time):
    now = time.time()
    diff = now - start_time
    if diff < 2.5: return
    percentage = current * 100 / total
    speed = current / diff
    bar = "▬" * int(percentage // 10) + "▭" * (10 - int(percentage // 10))
    tmp = (
        f"🚀 **Transferring.. جاري النقل**\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"◈ **Progress:** `{bar}` **{percentage:.1f}%**\n"
        f"◈ **Speed:** `{speed/(1024*1024):.2f} MB/s` ⚡️\n"
        f"◈ **Size:** `{current/(1024*1024):.1f}` / `{total/(1024*1024):.1f} MB`\n\n"
        f"━━━━━━━━━━━━━━━━━━"
    )
    try: await status_msg.edit(tmp)
    except: pass

# --- Handlers | الأوامر ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if not await check_subscription(client, message): return
    add_user(message.from_user.id)
    kb = [['🔄 Restart Service | بدء الخدمة'], ['👨‍💻 Developer | المطور']]
    if message.from_user.id == ADMIN_ID: kb[1].append('📣 Broadcast | إذاعة')
    
    welcome_text = (
        f"✨━━━━━━━━━━━━━✨\n"
        f"  🙋‍♂️ Welcome | أهلاً بك يا **{message.from_user.first_name}**\n"
        f"  🌟 In **{BOT_NAME}** World\n"
        f"✨━━━━━━━━━━━━━✨\n\n"
        f"🚀 **Fast Downloader for | بوت تحميل سريع:**\n"
        f"📹 YouTube | 📸 Instagram | 🎵 TikTok\n"
        f"👻 Snapchat | 🔵 Facebook\n\n"
        f"👇 **Send link now! | أرسل الرابط الآن!**"
    )
    await message.reply(welcome_text, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

@app.on_message(filters.text & filters.private)
async def handle_text(client, message):
    if not await check_subscription(client, message): return
    text, user_id = message.text, message.from_user.id
    
    if text == '🔄 Restart Service | بدء الخدمة':
        await message.reply("📡 **System Ready.. النظام جاهز!** ⚡️")
        return
    
    if text == '👨‍💻 Developer | المطور':
        msg = f"👑 **Main Developer:** {DEV_USER}\n📢 **Our Channel:** @{CHANNEL_USER}\n"
        if user_id == ADMIN_ID: msg += f"📊 **Total Users:** `{get_users_count()}`"
        await message.reply(msg)
        return

    if text == '📣 Broadcast | إذاعة' and user_id == ADMIN_ID:
        await message.reply("📥 **Send your message | أرسل رسالة الإذاعة:**")
        user_cache[f"bc_{user_id}"] = True
        return

    if user_cache.get(f"bc_{user_id}"):
        if os.path.exists(USERS_FILE):
            users = open(USERS_FILE).read().splitlines()
            for u in users:
                try: await message.copy(int(u))
                except: pass
            await message.reply("✅ **Broadcast Sent | تمت الإذاعة**")
        user_cache[f"bc_{user_id}"] = False
        return

    if "http" in text:
        status = await message.reply("🔍 **Analyzing.. جاري المعالجة** ⏳")
        try:
            formats = await asyncio.to_thread(get_all_formats, text)
            user_cache[user_id] = text
            btns = [[InlineKeyboardButton(res, callback_data=fid)] for res, fid in formats.items()]
            await status.edit("✅ **Formats Found | تم الاستخراج**\nChoose your option: 👇", reply_markup=InlineKeyboardMarkup(btns))
        except: await status.edit("❌ **Error | فشل المعالجة**")

@app.on_callback_query()
async def download_cb(client, callback_query):
    f_id, user_id = callback_query.data, callback_query.from_user.id
    url = user_cache.get(user_id)
    if not url:
        await callback_query.answer("⚠️ Session Expired", show_alert=True); return
    
    await callback_query.message.edit("⚙️ **Processing.. جاري التنفيذ**\n━━━━━━━━━━━━━━━━━━\n📡 **Status:** `Direct Connection` ⚡️\n⏳ **Please wait.. يرجى الانتظار**")
    is_audio = "audio" in f_id
    file_path = f"media_{user_id}.{'m4a' if is_audio else 'mp4'}"
    
    try:
        await asyncio.to_thread(run_download, url, f_id, file_path)
        if os.path.exists(file_path):
            st = time.time()
            if is_audio: 
                await client.send_audio(user_id, file_path, caption=f"🎵 **Audio by {BOT_NAME}**", progress=progress_bar, progress_args=(callback_query.message, st))
            else: 
                await client.send_video(user_id, file_path, caption=f"🎬 **Video by {BOT_NAME}**", progress=progress_bar, progress_args=(callback_query.message, st))
            
            # رسالة الانتهاء المطلوبة
            final_msg = (
                f"✨ **Mission Completed | تمت المهمة** ✨\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🤖 **Bot:** `{BOT_NAME}`\n"
                f"👨‍💻 **Dev:** {DEV_USER}\n\n"
                f"🌟 **شكراً لاستخدامك خدمتنا!**\n"
                f"📢 **Channel:** @{CHANNEL_USER}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🚀 *Fast • Simple • High Quality*"
            )
            await client.send_message(user_id, final_msg)
            await callback_query.message.delete()
    except Exception as e: 
        await callback_query.message.edit(f"❌ **Failed:** {e}")
    finally: 
        if os.path.exists(file_path): os.remove(file_path)

# --- Main Execution ---
if __name__ == "__main__":
    # تشغيل خادم الويب في الخلفية
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # تشغيل البوت
    print("Bot is starting...")
    app.run()
