import os
import telebot
import bot  # استيراد ملف bot.py ككامل

# جلب المفاتيح من متغيرات البيئة في Railway بأمان
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# تهيئة البوت
bot_instance = telebot.TeleBot(BOT_TOKEN)

# دالة التعامل مع الرسائل
@bot_instance.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    bot.create_user(user_id) # استخدام دالة من ملف bot.py
    bot_instance.reply_to(message, "مرحباً بك في البوت! أنا جاهز لمساعدتك.")

@bot_instance.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.chat.id)
    
    # التحقق من المستخدم واليوم
    bot.reset_daily(user_id)
    
    # مثال لاستخدام الدوال التي في bot.py
    # هنا يمكنك إضافة منطق الاتصال بـ Groq باستخدام GROQ_API_KEY
    
    bot.save(user_id, "user", message.text)
    bot.increase_count(user_id)
    
    # هنا يتم استدعاء المنطق الخاص بالرد (بدلاً من دالة chat الملغاة)
    bot_instance.reply_to(message, "تم استلام رسالتك وتخزينها في قاعدة البيانات.")

# تشغيل البوت
if __name__ == "__main__":
    print("البوت يعمل الآن...")
    bot_instance.polling()
