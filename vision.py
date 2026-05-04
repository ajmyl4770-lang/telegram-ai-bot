import base64
import requests
from config import OPENAI_API_KEY

def analyze_image(image_path):
    try:
        with open(image_path, "rb") as img:
            base64_image = base64.b64encode(img.read()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "حلل الصورة واذكر المشكلة التقنية."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        # 🔥 هنا أهم شيء
        if response.status_code != 200:
            return f"❌ API ERROR:\n{response.text}"

        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"❌ EXCEPTION:\n{str(e)}"
