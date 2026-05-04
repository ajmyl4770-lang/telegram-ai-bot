from groq import Groq
from config import GROQ_API_KEY, MODEL
from db import save, history

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
أنت مساعد ذكي عربي اسمه أبو جميل.
تساعد في صيانة الهواتف وتقديم حلول تقنية.
لا تخترع معلومات.
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
