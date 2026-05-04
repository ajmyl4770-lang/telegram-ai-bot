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
    create_user(user_id)
    reset_daily(user_id)

    user = get_user(user_id)
    vip = user[1]
    count = user[2]

    # 🔴 حد المستخدم المجاني
    if vip == 0 and count >= FREE_LIMIT:
        return "🚫 انتهى الحد المجاني اليوم. قم بالترقية إلى VIP للاستمرار."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history(user_id),
        {"role": "user", "content": text}
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2
    )

    reply = response.choices[0].message.content.strip()

    save(user_id, "user", text)
    save(user_id, "assistant", reply)

    if vip == 0:
        increase_count(user_id)

    return reply
