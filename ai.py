from groq import Groq
import config

client = Groq(api_key=config.GROQ_API_KEY)

def chat(messages):
    try:
        response = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print("GROQ API INTERNAL ERROR:", e)
        return "⚠️ عذراً، واجه المحرك خطأ داخلي أثناء توليد النص."
