from PIL import Image
import pytesseract
from config import GROQ_API_KEY
from groq import Groq

client = Groq(api_key=GROQ_API_KEY)

def analyze_image(image_path):
    try:
        # 🧠 1) استخراج النص من الصورة (OCR)
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang="eng")

        if not text.strip():
            text = "لا يوجد نص واضح في الصورة"

        # 🧠 2) تحليل النص عبر Groq
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "أنت مساعد تقني تحلل محتوى الصور بشكل مبسط."
                },
                {
                    "role": "user",
                    "content": f"حلل محتوى الصورة التالي واشرحه:\n\n{text}"
                }
            ],
            temperature=0.5
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"خطأ في تحليل الصورة: {str(e)}"
