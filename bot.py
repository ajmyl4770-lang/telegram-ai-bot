import os
import io
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- إعداد السيرفر الوهمي لإبقاء البوت مستيقظاً ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- إعدادات التوكنات (سيتم جلبها من إعدادات Render) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_API_TOKEN}"}

# روابط النماذج
MODELS = {
    "image": "https://huggingface.co",
    "video": "https://huggingface.co",
    "music": "https://huggingface.co"
}

def query_hf(prompt, model_url):
    try:
        response = requests.post(model_url, headers=HEADERS, json={"inputs": prompt}, timeout=120)
        if response.status_code == 200:
            return response.content
    except:
        return None
    return None

# --- أوامر البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 بوت الذكاء الاصطناعي الشامل يعمل!\n\nاستخدم الأوامر:\n/image [وصف]\n/video [وصف]\n/music [وصف]")

async def image_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("اكتب وصفاً للصورة")
    await update.message.reply_text("🎨 جاري التصميم...")
    result = query_hf(prompt, MODELS["image"])
    if result: await update.message.reply_photo(photo=io.BytesIO(result))
    else: await update.message.reply_text("❌ السيرفر مضغوط، حاول مجدداً")

async def music_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("اكتب وصفاً للموسيقى")
    await update.message.reply_text("🎵 جاري التأليف...")
    result = query_hf(prompt, MODELS["music"])
    if result: await update.message.reply_audio(audio=io.BytesIO(result), filename="music.mp3")
    else: await update.message.reply_text("❌ فشل التوليد")

async def video_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt: return await update.message.reply_text("اكتب وصفاً للفيديو")
    await update.message.reply_text("🎬 جاري إنتاج الفيلم...")
    result = query_hf(prompt, MODELS["video"])
    if result: await update.message.reply_video(video=io.BytesIO(result))
    else: await update.message.reply_text("❌ السيرفر مشغول حالياً")

# --- تشغيل البوت ---
if __name__ == '__main__':
    keep_alive() # تشغيل السيرفر الوهمي
    bot = Application.builder().token(TELEGRAM_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("image", image_cmd))
    bot.add_handler(CommandHandler("music", music_cmd))
    bot.add_handler(CommandHandler("video", video_cmd))
    print("Bot is running...")
    bot.run_polling()
