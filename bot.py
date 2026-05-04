from groq import Groq
from config import GROQ_API_KEY, MODEL
from db import save, history, touch_user

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
أنت "أبو جميل"، مساعد دعم فني احترافي ضمن نظام شركة تقنية.

المهام:
- حل مشاكل الهواتف والبرمجيات
- تقديم حلول دقيقة وسريعة
- شرح الخطوات بشكل واضح

القواعد:
- اجعل الرد مختصر وعملي
- لا تطيل الكلام
- لا تعطي معلومات غير مؤكدة
- إذا المشكلة غير واضحة اسأل سؤال واحد فقط
"""

def chat(user_id, text):
    touch_user(user_id)

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

    return reply
