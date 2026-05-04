from groq import Groq
from config import GROQ_API_KEY, MODEL
from db import (
    create_user, get_user, reset_daily,
    save, history, increase_count, FREE_LIMIT
)

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
أنت "أبو جميل" مساعد تقني احترافي لنظام مدفوع.

القواعد:
- ردود مختصرة وذكية
- حلول مباشرة
- بدون حشو
"""

def chat(user_id, text):
    try:
        # 🧠 إنشاء المستخدم إذا جديد
        create_user(user_id)

        # 🔄 إعادة ضبط الحد اليومي
        reset_daily(user_id)

        user = get_user(user_id)
        vip = user[1]        # 0 = عادي / 1 = VIP
        count = user[2]      # عدد الرسائل

        # 🚫 منع المستخدم إذا تجاوز الحد
        if vip == 0 and count >= FREE_LIMIT:
            return "🚫 انتهى الحد المجاني اليوم.\n💎 اشترك VIP للاستمرار بدون حدود."

        # 🧠 تحديد مستوى الذكاء حسب VIP
        temp = 0.3 if vip else 0.2

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history(user_id),
            {"role": "user", "content": text}
        ]

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temp
        )

        reply = response.choices[0].message.content.strip()

        # 💾 حفظ المحادثة
        save(user_id, "user", text)
        save(user_id, "assistant", reply)

        # ➕ زيادة العداد للمستخدم العادي فقط
        if vip == 0:
            increase_count(user_id)

        return reply

    except Exception as e:
        return "⚠️ حدث خطأ مؤقت، حاول مرة أخرى لاحقاً."
