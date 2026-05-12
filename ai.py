from groq import Groq
from config import GROQ_API_KEY, MODEL

client = Groq(api_key=GROQ_API_KEY)

SYSTEM = {
    "role": "system",
    "content": "أنت مساعد عربي ذكي، مختصر، واضح، واحترافي."
}

def chat(messages):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[SYSTEM] + messages,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ خطأ: {str(e)}"
