import telebot
from telebot import types
import config
import database as db
from ai import chat
from image_ai import generate_image 
from gtts import gTTS
import os
import traceback

# استدعاء مكتبة معالجة الوسائط الحديثة والمتوافقة مع السيرفر
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ImageClip
from moviepy.audio.AudioClip import CompositeAudioClip

bot = telebot.TeleBot(config.BOT_TOKEN, num_threads=4)
user_mode = {}

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_chat = types.KeyboardButton("💬 دردشة ذكية")
    btn_image = types.KeyboardButton("🎨 توليد صورة")
    btn_music = types.KeyboardButton("🎵 إنشاء أغنية صوتاً")
    btn_video = types.KeyboardButton("🎬 إنشاء فيديو غنائي")
    btn_stats = types.KeyboardButton("📊 الإحصائيات")
    btn_clear = types.KeyboardButton("🧹 مسح الذاكرة")
    markup.add(btn_chat, btn_image, btn_music, btn_video, btn_stats, btn_clear)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    db.create_user(user_id)
    user_mode[user_id] = "chat"
    text = "👋 أهلاً بك في مركز بن علي المتطور للذكاء الصناعي 🌟\n\n📌 اختر الخدمة المطلوبة عبر الأزرار أدناه للبدء الفوري."
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "🎨 توليد صورة")
def image_init(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "image"
    bot.reply_to(message, "🎨 اكتب وصف الصورة التي تريد رسمها الآن (مثال: اسد في غابة خيالية):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda msg: msg.text == "🎵 إنشاء أغنية صوتاً")
def music_init(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "music"
    bot.reply_to(message, "🎵 اكتب فكرة اللحن ونوعه (مثال: شيلة حماس، لحن يمني):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda msg: msg.text == "🎬 إنشاء فيديو غنائي")
def video_init(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "video"
    bot.reply_to(message, "🎬 اكتب موضوع الفيديو ونوع اللحن الخلفي:", reply_markup=types.ReplyKeyboardRemove())

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
    bot.reply_to(message, "🧹 تم تصفير ذاكرة المحادثة بنجاح.", reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "💬 دردشة ذكية")
def set_chat_mode(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "chat"
    bot.reply_to(message, "💬 وضع الدردشة نشط الآن، تفضل بإرسال سؤالك مباشرة.", reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle(message):
    user_id = str(message.chat.id)
    text = message.text
    mode = user_mode.get(user_id, "chat")

    try:
        db.create_user(user_id)
        db.reset_daily(user_id)

        # ---------------- وضع توليد الصور ----------------
        if mode == "image":
            bot.send_chat_action(message.chat.id, "upload_photo")
            try:
                image_url = generate_image(text)
                bot.send_photo(message.chat.id, image_url, caption=f"🎨 صورتك جاهزة:\n✨ `{text}`", reply_markup=main_keyboard())
            except Exception as img_err:
                bot.reply_to(message, "⚠️ فشل محرك الصور في معالجة طلبك.", reply_markup=main_keyboard())
            user_mode[user_id] = "chat"
            return

        # ---------------- وضع الوسائط (صوت وفيديو) ----------------
        if mode in ["music", "video"]:
            bot.send_chat_action(message.chat.id, "upload_audio")
            prompt = f"اكتب كلمات قصيرة بأسلوب شيلة أو أغنية عربية من 4 أسطر فقط مقفاة وبدون حركات تشكيل عن: {text}"

            try:
                lyrics = chat([{"role": "user", "content": prompt}])
                tts_file = f"tts_{user_id}.mp3"
                final_audio = f"{user_id}.mp3"
                video_file = f"{user_id}.mp4"

                tts = gTTS(text=lyrics, lang="ar")
                tts.save(tts_file)

                # دمج الموسيقى المرفوعة محلياً تلقائياً
                bg_music_file = "shilat.mp3"
                lower_text = text.lower()
                if "يمن" in lower_text: bg_music_file = "yemen.mp3"
                elif "خليج" in lower_text: bg_music_file = "gulf.mp3"
                elif "مصر" in lower_text: bg_music_file = "egypt.mp3"

                if os.path.exists(bg_music_file):
                    voice_clip = AudioFileClip(tts_file)
                    bg_clip = AudioFileClip(bg_music_file).with_duration(voice_clip.duration).volumex(0.3)
                    combined_audio = CompositeAudioClip([bg_clip, voice_clip])
                    combined_audio.write_audiofile(final_audio, logger=None)
                    voice_clip.close()
                    bg_clip.close()
                    combined_audio.close()
                else:
                    os.rename(tts_file, final_audio)

                if os.path.exists(tts_file): os.remove(tts_file)

                if mode == "music":
                    with open(final_audio, "rb") as audio:
                        bot.send_audio(message.chat.id, audio, title="AI Dynamic Track", caption=f"📝 الكلمات:\n{lyrics}", reply_markup=main_keyboard())
                    if os.path.exists(final_audio): os.remove(final_audio)
                
                elif mode == "video":
                    bg_image = "background.jpg"
                    if os.path.exists(bg_image):
                        try:
                            bot.send_chat_action(message.chat.id, "upload_video")
                            audio_clip = AudioFileClip(final_audio)
                            video_clip = ImageClip(bg_image).with_duration(audio_clip.duration)
                            video_clip = video_clip.with_audio(audio_clip)
                            
                            video_clip.write_videofile(video_file, fps=1, codec="libx264", audio_codec="aac", logger=None)
                            audio_clip.close()
                            video_clip.close()

                            with open(video_file, "rb") as video:
                                bot.send_video(message.chat.id, video, caption=f"🎬 فيديو جاهز!\n\n📝 الكلمات:\n{lyrics}", reply_markup=main_keyboard())
                            if os.path.exists(video_file): os.remove(video_file)
                        except Exception as render_err:
                            with open(final_audio, "rb") as audio:
                                bot.send_audio(message.chat.id, audio, title="AI Track", caption=f"🎵 تم إرسالها كصوت لتعذر دمج الفيديو بالسيرفر.\n\n📝 الكلمات:\n{lyrics}", reply_markup=main_keyboard())
                    else:
                        with open(final_audio, "rb") as audio:
                            bot.send_audio(message.chat.id, audio, title="AI Track", caption=f"⚠️ يرجى رفع صورة `background.jpg` لتفعيل الفيديو.\n\n📝 الكلمات:\n{lyrics}", reply_markup=main_keyboard())
                    
                    if os.path.exists(final_audio): os.remove(final_audio)

            except Exception as media_err:
                print("MEDIA ERR:", media_err)
                bot.reply_to(message, "⚠️ فشل إنتاج وتراكب الوسائط، يرجى إعادة المحاولة.", reply_markup=main_keyboard())

            user_mode[user_id] = "chat"
            return

        # ---------------- وضع الدردشة العادية ----------------
        history_data = db.history(user_id)
        history_data.append({"role": "user", "content": text})

        response = chat(history_data)

        db.save(user_id, "user", text)
        db.save(user_id, "assistant", response)
        db.increase_count(user_id)

        bot.reply_to(message, response, reply_markup=main_keyboard())

    except Exception as main_err:
        print("MAIN HANDLER ERROR:", main_err)
        traceback.print_exc()
        bot.reply_to(message, "⚠️ واجه السيرفر مشكلة مؤقتة في معالجة طلبك.", reply_markup=main_keyboard())

print("🤖 Bot Running Successfully with Local Audios...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
