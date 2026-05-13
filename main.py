import telebot
from telebot import types
import config
import database as db
from ai import chat
from gtts import gTTS
import os
import traceback

# تفعيل التعدد الخيطي بشكل آمن
bot = telebot.TeleBot(config.BOT_TOKEN, num_threads=4)

user_mode = {}

# دالة لتوليد لوحة الأزرار الرئيسية
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_chat = types.KeyboardButton("💬 دردشة ذكية")
    btn_music = types.KeyboardButton("🎵 إنشاء أغنية")
    btn_stats = types.KeyboardButton("📊 الإحصائيات")
    btn_clear = types.KeyboardButton("🧹 مسح الذاكرة")
    markup.add(btn_chat, btn_music, btn_stats, btn_clear)
    return markup

# =========================
# START
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
# CONTROLS VIA BUTTONS / COMMANDS
# =========================
@bot.message_handler(func=lambda msg: msg.text in ["🎵 إنشاء أغنية", "/music"])
def music_init(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "music"
    
    # إزالة الأزرار مؤقتاً ليركز المستخدم على كتابة الفكرة
    remove_rm = types.ReplyKeyboardRemove()
    bot.reply_to(
        message,
        "🎵 اكتب فكرة الأغنية الآن (مثال: شيلة حماس، راب يمني، أغنية حب):",
        reply_markup=remove_rm
    )

@bot.message_handler(func=lambda msg: msg.text in ["📊 الإحصائيات", "/stats"])
def stats(message):
    user_id = str(message.chat.id)
    user = db.get_user(user_id)

    if not user:
        bot.reply_to(message, "⚠️ لا توجد بيانات مسجلة لك بعد.")
        return

    text = f"""
📊 إحصائياتك الحالية:

👤 معرفك: {user_id}
💬 عدد الرسائل: {user[2]}
⭐ حساب VIP: {'نعم' if user[1] else 'لا'}
"""
    bot.reply_to(message, text, reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text in ["🧹 مسح الذاكرة", "/clear"])
def clear_history(message):
    user_id = str(message.chat.id)
    
    # أداء الاستعلام داخل ملف database لحماية الخيوط البرمجية
    db.clear_user_messages(user_id) 
    user_mode[user_id] = "chat"

    bot.reply_to(message, "🧹 تم مسح ذاكرة المحادثة بنجاح والأزرار جاهزة.", reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "💬 دردشة ذكية")
def set_chat_mode(message):
    user_id = str(message.chat.id)
    user_mode[user_id] = "chat"
    bot.reply_to(message, "💬 وضع الدردشة نشط الآن، تفضل بإرسال سؤالك.", reply_markup=main_keyboard())

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

        # ================= وضع الموسيقى =================
        if mode == "music":
            bot.send_chat_action(message.chat.id, "upload_audio")

            prompt = f"اكتب أغنية عربية قوية من 8 إلى 12 سطر.\nالستايل: راب، شيلات، شعبي، خليجي، يمني.\nبدون مبالغة وتكرار.\nالموضوع:\n{text}"

            try:
                lyrics = chat([{"role": "user", "content": prompt}])
                file_name = f"{user_id}.mp3"

                tts = gTTS(text=lyrics, lang="ar")
                tts.save(file_name)

                with open(file_name, "rb") as audio:
                    bot.send_audio(
                        message.chat.id,
                        audio,
                        title="🎵 AI Song",
                        caption="🎧 تم إنشاء كلمات اللحن الصوتي بنجاح!",
                        reply_markup=main_keyboard()
                    )

                os.remove(file_name)

            except Exception as e:
                print("MUSIC ERROR:", e)
                traceback.print_exc()
                bot.reply_to(message, "⚠️ حدث خطأ أثناء معالجة الملف الصوتي.", reply_markup=main_keyboard())

            user_mode[user_id] = "chat"
            return

        # ================= وضع الدردشة =================
        history = db.history(user_id)
        history.append({"role": "user", "content": text})

        try:
            response = chat(history)
        except Exception as e:
            print("AI ERROR:", e)
            traceback.print_exc()
            response = "⚠️ الذكاء الاصطناعي مشغول حالياً، يرجى المحاولة لاحقاً."

        db.save(user_id, "user", text)
        db.save(user_id, "assistant", response)
        db.increase_count(user_id)

        bot.reply_to(message, response, reply_markup=main_keyboard())

    except Exception as e:
        print("MAIN ERROR:", e)
        traceback.print_exc()
        bot.reply_to(message, "⚠️ حدث خطأ غير متوقع.", reply_markup=main_keyboard())

# =========================
# RUN BOT
# =========================
print("🤖 Bot Running Successfully...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
