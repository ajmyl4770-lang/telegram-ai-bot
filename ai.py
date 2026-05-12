from groq import Groq
from config import GROQ_API_KEY, MODEL

client = Groq(api_key=GROQ_API_KEY)

def chat(history):
    try:
        messages = [
            {
                "role": "system",
                "content": "أنت مساعد ذكي عربي، مختصر، واضح، وتجيب بدون إطالة."
            }
        ]

        messages.extend(history)

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ خطأ في الذكاء الاصطناعي: {str(e)}"
