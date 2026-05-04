from groq import Groq
from config import GROQ_API_KEY, MODEL
from db import save, history

client = Groq(api_key=GROQ_API_KEY)
SYSTEM_PROMPT = """
أنت مساعد ذكي عربي اسمه "أبو جميل".

المعلومات الرسمية:
- الاسم الحقيقي للمطور: فتحي على الأشول
- التخصص: مهندس أكاديمي في صيانة الهاتف النقال
- الجهة: مركز بن علي التكنولوجي
- الموقع: مديرية مستبأ - سوق الهيجة

دورك:
- مساعدة المستخدمين في مشاكل الهواتف والتقنية
- تقديم حلول مختصرة ودقيقة
- الرد بلغة عربية واضحة وبسيطة

ملاحظة:
يمكن التواصل مع المطور عبر قنواته الرسمية عند الحاجة.
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
        temperature=0.4
    )

    reply = response.choices[0].message.content.strip()

    save(user_id, "user", text)
    save(user_id, "assistant", reply)

    return reply
