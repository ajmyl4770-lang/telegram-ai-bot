import telebot
from telebot import types
import config
import database as db
from ai import chat
from gtts import gTTS
import os
import traceback

# استدعاءات مكتبة MoviePy المتوافقة مع الإصدار الجديد 2.0+ لمنع خطأ ModuleNotFoundError
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ImageClip

# تفعيل التعدد الخيطي بشكل آمن مع 4 خيوط معالجة لسرعة الاستجابة على Railway
bot = telebot.TeleBot(config.BOT_TOKEN, num_threads=4)

user_mode = {}

def main_keyboard():
    """توليد لوحة أزرار التحكم الرئيسية أسفل الشاشة للمستخدم"""
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
👋 أهلاً بك يا أبو جميل 🌟
🤖 مركز بن علي للذكاء الصناعي برتبته الجديدة!

📌 تصفح الخدمات عبر الأزرار أدناه للبدء مباشرة.
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
    bot.reply_to(message, "🎬 اكتب موضوع الفيديو ولون الأغنية (شيلة، راب، يمني):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda msg: msg.text == "📊 الإحصائيات")
def stats(message):
    user_id = str(message.chat.id)
    user = db.get_user(user_id)
    if not user:
        bot.reply_to(message, "⚠️ لا توجد بيانات مسجلة لك بعد.", reply_markup=main_keyboard())
        return
    text = f"📊 إحصائياتك:\n\n👤 معرفك: {user_id}\n🔄 الاستخدام اليومي: {user[2]} رسائل\n⭐ VIP: {'نعم' if user[1] == 1 else 'لا'}"
    bot.reply_to(message, text, reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "🧹 مسح الذاكرة")
def clear_history(message):
    user_id = str(message.chat.id)
    db.clear_user_messages(user_id) 
    user_mode[user_id] = "chat"
    bot.reply_to(message, "🧹 تم تصفير الذاكرة بنجاح والأزرار جاهزة.", reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "💬 دردشة ذكية")
def set_chat_mode(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "chat"
    bot.reply_to(message, "💬 وضع الدردشة نشط الآن، تفضل بإرسال سؤالك مباشرة.", reply_markup=main_keyboard())

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

                # 1. إنشاء الملف الصوتي الأساسي عبر gTTS
                tts = gTTS(text=lyrics, lang="ar")
                tts.save(audio_file)

                # إذا طلب المستخدم ملف صوتي فقط
                if mode == "music":
                    with open(audio_file, "rb") as audio:
                        bot.send_audio(message.chat.id, audio, title="AI Song", caption=f"🎧 كلمات الأغنية:\n{lyrics}", reply_markup=main_keyboard())
                    os.remove(audio_file)
                
                # إذا طلب المستخدم مقطع فيديو كامل
                elif mode == "video":
                    bg_image = "background.jpg"
                    if os.path.exists(bg_image):
                        audio_clip = AudioFileClip(audio_file)
                        
                        # استخدام الدوال الجديدة المتوافقة مع تحديث MoviePy 2.0+ (.with_duration)
                        video_clip = ImageClip(bg_image).with_duration(audio_clip.duration)
                        video_clip = video_clip.with_audio(audio_clip)
                        
                        # معالجة وتصدير الفيديو بصيغة MP4 خفيفة وسريعة للبوتات
                        video_clip.write_videofile(video_file, fps=2, codec="libx264", audio_codec="aac", logger=None)
                        
                        audio_clip.close()
                        video_clip.close()

                        with open(video_file, "rb") as video:
                            bot.send_video(message.chat.id, video, caption=f"🎬 الفيديو الغنائي جاهز!\n\n📝 الكلمات:\n{lyrics}", reply_markup=main_keyboard())
                        os.remove(video_file)
                    else:
                        bot.reply_to(message, "⚠️ يرجى إضافة ملف صورة باسم `background.jpg` في مشروعك ليعمل نظام الفيديو بكفاءة.", reply_markup=main_keyboard())
                    os.remove(audio_file)

            except Exception as e:
                print("MEDIA GENERATION ERROR:", e)
                traceback.print_exc()
                bot.reply_to(message, "⚠️ تعذر معالجة وإنتاج الوسائط حالياً.", reply_markup=main_keyboard())

            user_mode[user_id] = "chat"
            return

        # ================= وضع الدردشة العادية =================
        history = db.history(user_id)
        history.append({"role": "user", "content": text})

        try:
            response = chat(history)
        except Exception as e:
            print("AI ERROR:", e)
            response = "⚠️ الذكاء الاصطناعي مشغول حالياً، حاول مجدداً لاحقاً."

        db.save(user_id, "user", text)
        db.save(user_id, "assistant", response)
        db.increase_count(user_id)

        bot.reply_to(message, response, reply_markup=main_keyboard())

    except Exception as e:
        print("MAIN ERROR:", e)
        traceback.print_exc()
        bot.reply_to(message, "⚠️ حدث خطأ مؤقت أثناء معالجة رسالتك.", reply_markup=main_keyboard())

# =========================
# RUN BOT
# =========================
print("🤖 Bot Running Successfully...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
