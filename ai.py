from groq import Groq
import config

client = Groq(api_key=config.GROQ_API_KEY)

def chat(messages):
    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content
