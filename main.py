import telebot
from telebot import types
import config
import database as db
from ai import chat
from gtts import gTTS
import os
import traceback
from moviepy.editor import AudioFileClip, ImageClip

bot = telebot.TeleBot(config.BOT_TOKEN, num_threads=4)

user_mode = {}

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_chat = types.KeyboardButton("💬 دردشة ذكية")
    btn_music = types.KeyboardButton("🎵 إنشاء أغنية صوتاً")
    btn_video = types.KeyboardButton("🎬 إنشاء فيديو غنائي")
    btn_stats = types.KeyboardButton("📊 الإحصائيات")
    btn_clear = types.KeyboardButton("🧹 مسح الذاكرة")
    markup.add(btn_chat, btn_music, btn_video, btn_stats, btn_clear)
    return markup

# =========================
# START COMMAND
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    db.create_user(user_id)
    user_mode[user_id] = "chat"

    text = """
👋 أهلاً بك في مركز بن علي للذكاء الصناعي المتطور 🌟

🎬 أصبح بإمكاني الآن تصميم مقاطع فيديو صوتية متكاملة!
📌 اختر الخدمة المطلوبة من الأزرار بالأسفل لبدء التشغيل الفوري.
"""
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())

# =========================
# CONTROLS VIA BUTTONS
# =========================
@bot.message_handler(func=lambda msg: msg.text == "🎵 إنشاء أغنية صوتاً")
def music_init(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "music"
    bot.reply_to(message, "🎵 اكتب فكرة الأغنية المطلوبة (ملف صوتي فقط):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda msg: msg.text == "🎬 إنشاء فيديو غنائي")
def video_init(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "video"
    bot.reply_to(message, "🎬 اكتب موضوع الفيديو ولون الأغنية (شيلة، راب، يمني) لتحويلها لمقطع فيديو:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda msg: msg.text in ["📊 الإحصائيات", "/stats"])
def stats(message):
    user_id = str(message.chat.id)
    user = db.get_user(user_id)
    if not user:
        bot.reply_to(message, "⚠️ لا توجد بيانات مسجلة لك بعد.", reply_markup=main_keyboard())
        return
    text = f"📊 إحصائياتك:\n\n👤 معرفك: {user_id}\n🔄 الاستخدام اليومي: {user[2]} رسائل\n⭐ VIP: {'نعم' if user[1] == 1 else 'لا'}"
    bot.reply_to(message, text, reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text in ["🧹 مسح الذاكرة", "/clear"])
def clear_history(message):
    user_id = str(message.chat.id)
    db.clear_user_messages(user_id) 
    user_mode[user_id] = "chat"
    bot.reply_to(message, "🧹 تم تصفير الذاكرة بنجاح.", reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "💬 دردشة ذكية")
def set_chat_mode(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "chat"
    bot.reply_to(message, "💬 وضع الدردشة نشط الآن.", reply_markup=main_keyboard())

# =========================
# MAIN TEXT HANDLER
# =========================
@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = str(message.chat.id)
    text = message.text
    mode = user_mode.get(user_id, "chat")

    try:
        db.create_user(user_id)
        db.reset_daily(user_id)

        # ================= وضع الصوت أو الفيديو =================
        if mode in ["music", "video"]:
            bot.send_chat_action(message.chat.id, "upload_video" if mode == "video" else "upload_audio")

            prompt = f"اكتب كلمات قوية ولحن منظم من 6 أسطر فقط.\nالستايل المطلوبة: {text}\nاكتب الكلمات مباشرة بدون مقدمات."

            try:
                lyrics = chat([{"role": "user", "content": prompt}])
                audio_file = f"{user_id}.mp3"
                video_file = f"{user_id}.mp4"

                # 1. إنشاء الصوت أولاً
                tts = gTTS(text=lyrics, lang="ar")
                tts.save(audio_file)

                if mode == "music":
                    with open(audio_file, "rb") as audio:
                        bot.send_audio(message.chat.id, audio, title="AI Song", caption=f"🎧 كلمات الأغنية:\n{lyrics}", reply_markup=main_keyboard())
                    os.remove(audio_file)
                
                elif mode == "video":
                    # 2. دمج الصوت مع خلفية صلبة لإنشاء فيديو MP4 مدمج بكفاءة
                    bg_image = "background.jpg" if os.path.exists("background.jpg") else None
                    
                    if bg_image:
                        audio_clip = AudioFileClip(audio_file)
                        video_clip = ImageClip(bg_image).set_duration(audio_clip.duration)
                        video_clip = video_clip.set_audio(audio_clip)
                        video_clip.write_videofile(video_file, fps=2, codec="libx264", audio_codec="aac", logger=None)
                        
                        audio_clip.close()
                        video_clip.close()

                        with open(video_file, "rb") as video:
                            bot.send_video(message.chat.id, video, caption=f"🎬 الفيديو الغنائي جاهز!\n\n📝 الكلمات:\n{lyrics}", reply_markup=main_keyboard())
                        
                        os.remove(video_file)
                    else:
                        bot.reply_to(message, "⚠️ يرجى إضافة ملف صورة باسم `background.jpg` في خادم البوت ليعمل نظام الفيديو بكفاءة.", reply_markup=main_keyboard())
                    
                    os.remove(audio_file)

            except Exception as e:
                print("MEDIA GENERATION ERROR:", e)
                bot.reply_to(message, "⚠️ تعذر معالجة الوسائط حالياً.", reply_markup=main_keyboard())

            user_mode[user_id] = "chat"
            return

        # ================= وضع الدردشة العادية =================
        history = db.history(user_id)
        history.append({"role": "user", "content": text})

        try:
            response = chat(history)
        except Exception as e:
            response = "⚠️ الذكاء الاصطناعي مشغول حالياً"

        db.save(user_id, "user", text)
        db.save(user_id, "assistant", response)
        db.increase_count(user_id)

        bot.reply_to(message, response, reply_markup=main_keyboard())

    except Exception as e:
        print("MAIN ERROR:", e)
        bot.reply_to(message, "⚠️ حدث خطأ مؤقت", reply_markup=main_keyboard())

# =========================
# RUN BOT
# =========================
print("🤖 Bot Running Successfully with Video Engine...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
