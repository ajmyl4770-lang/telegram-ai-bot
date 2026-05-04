from groq import Groq
from config import GROQ_API_KEY, MODEL
from db import save, history

client = Groq(api_key=GROQ_API_KEY)
SYSTEM_PROMPT = """
أنت "أبو جميل"، مساعد تقني ذكي ضمن نظام شركة احترافي لصيانة الهواتف والتقنية.

الدور:
- تقديم حلول تقنية دقيقة ومباشرة
- مساعدة المستخدمين في مشاكل الهواتف والبرمجيات
- شرح الحلول بشكل خطوات واضحة

قواعد الرد:
- لا تطيل الكلام
- لا تكرر المقدمة
- ابدأ مباشرة بالحل
- إذا المشكلة غير واضحة اطلب توضيح بسيط
- استخدم أسلوب احترافي شبيه بمساعدين الشركات

المستوى:
- تعمل كمساعد ضمن نظام دعم فني (Technical Support Assistant)
"""
def chat(user_id, text):
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
