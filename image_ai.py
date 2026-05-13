import urllib.parse

def generate_image(prompt):
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        # إضافة https:// في أول الرابط لكي يقبله تيليجرام ويرسل الصورة فوراً
        image_url = f"pollinations.ai{encoded_prompt}?width=1024&height=1024&nologo=true&seed=42"
        return image_url
    except Exception as e:
        print("Error inside image generation:", e)
        return "⚠️ تعذر الاتصال بمحرك توليد الصور حالياً."
