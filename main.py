import telebot
from telebot import types
import config
import database as db
from ai import chat
from gtts import gTTS
import os
import traceback

# الاستدعاءات الحديثة المتوافقة كلياً مع الإصدار الجديد لـ MoviePy ومنع خطأ الـ editor
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ImageClip

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
# COMMANDS
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    db.create_user(user_id)
    user_mode[user_id] = "chat"
    text = "👋 أهلاً بك يا أبو جميل 🌟\n🤖 مركز بن علي للذكاء الصناعي جاهز لخدمتك!\n\n📌 تصفح الخدمات عبر الأزرار أدناه للبدء مباشرة."
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())

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
    text = f"📊 إحصائياتك:\n\n👤 معرفك: {user_id}\n🔄 الاستخدام اليومي: {user} رسائل\n⭐ VIP: {'نعم' if user == 1 else 'لا'}"
    bot.reply_to(message, text, reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "🧹 مسح الذاكرة")
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

        if mode in ["music", "video"]:
            bot.send_chat_action(message.chat.id, "upload_audio")
            
            prompt = f"اكتب كلمات قوية شيلة أو أغنية عربية منظمة ومقفاة من 6 أسطر فقط عن موضوع: {text}. اكتب الكلمات مباشرة وبدون أي مقدمات أو هوامش."

            try:
                lyrics = chat([{"role": "user", "content": prompt}])
                audio_file = f"{user_id}.mp3"
                video_file = f"{user_id}.mp4"

                # توليد الصوت عبر gTTS
                tts = gTTS(text=lyrics, lang="ar")
                tts.save(audio_file)

                # 1. وضع الصوت فقط
                if mode == "music":
                    with open(audio_file, "rb") as audio:
                        bot.send_audio(message.chat.id, audio, title="AI Song", caption=f"🎧 كلمات الأغنية:\n{lyrics}", reply_markup=main_keyboard())
                    if os.path.exists(audio_file): os.remove(audio_file)
                
                # 2. وضع الفيديو الغنائي
                elif mode == "video":
                    bg_image = "background.jpg"
                    
                    if os.path.exists(bg_image):
                        try:
                            bot.send_chat_action(message.chat.id, "upload_video")
                            
                            audio_clip = AudioFileClip(audio_file)
                            
                            # استخدام دوال الجيل الجديد البرمجية .with_duration و .with_audio
                            video_clip = ImageClip(bg_image).with_duration(audio_clip.duration)
                            video_clip = video_clip.with_audio(audio_clip)
                            
                            # التصدير المتوافق مع الإصدار الحديث لـ MoviePy
                            video_clip.write_videofile(
                                video_file, 
                                fps=1, 
                                codec="libx264", 
                                audio_codec="aac"
                            )
                            
                            audio_clip.close()
                            video_clip.close()

                            with open(video_file, "rb") as video:
                                bot.send_video(message.chat.id, video, caption=f"🎬 الفيديو الغنائي جاهز!\n\n📝 الكلمات:\n{lyrics}", reply_markup=main_keyboard())
                            
                            if os.path.exists(video_file): os.remove(video_file)
                            if os.path.exists(audio_file): os.remove(audio_file)
                            
                        except Exception as video_err:
                            print("Video Render Fail, falling back to Audio:", video_err)
                            with open(audio_file, "rb") as audio:
                                bot.send_audio(message.chat.id, audio, title="AI Song (Audio Mode)", caption=f"🎧 تعذر دمج الفيديو فتم إرسالها كصوت.\n\n📝 الكلمات:\n{lyrics}", reply_markup=main_keyboard())
                            if os.path.exists(audio_file): os.remove(audio_file)
                    else:
                        with open(audio_file, "rb") as audio:
                            bot.send_audio(message.chat.id, audio, title="AI Song (Audio Mode)", caption=f"⚠️ يرجى رفع ملف صورة باسم `background.jpg` لتفعيل نظام الفيديو.\n\n📝 الكلمات:\n{lyrics}", reply_markup=main_keyboard())
                        if os.path.exists(audio_file): os.remove(audio_file)

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
            response = "⚠️ الذكاء الاصطناعي مشغول حالياً"

        db.save(user_id, "user", text)
        db.save(user_id, "assistant", response)
        db.increase_count(user_id)

        bot.reply_to(message, response, reply_markup=main_keyboard())

    except Exception as e:
        print("MAIN ERROR:", e)
        traceback.print_exc()
        bot.reply_to(message, "⚠️ حدث خطأ مؤقت أثناء معالجة رسالتك.", reply_markup=main_keyboard())

print("🤖 Bot Running Successfully...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
