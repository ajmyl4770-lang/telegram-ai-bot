from groq import Groq
from config import GROQ_API_KEY, MODEL

client = Groq(api_key=GROQ_API_KEY)

SYSTEM = {
    "role": "system",
    "content": "أنت مساعد عربي ذكي مختصر وواضح."
}

def chat(messages):
    try:
        res = client.chat.completions.create(
            model=MODEL,
            messages=[SYSTEM] + messages,
            temperature=0.7
        )
        return res.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ خطأ: {str(e)}"
