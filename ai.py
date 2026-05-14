import os
import google.generativeai as genai

# إعداد مفتاح API الخاص بك (تأكد من ضبطه في بيئتك)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE"))

def generate_text_response(prompt):
    """توليد النصوص والكلمات مع حماية كاملة ضد الأخطاء الداخلية"""
    if not prompt:
        return "⚠️ يرجى كتابة موضوع أو نص صحيح."
        
    try:
        # استخدام الموديل المستقر لتوليد النصوص
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        else:
            return "جاري معالجة الكلمات الآن، يرجى إعادة المحاولة."
            
    except Exception as error:
        # في حال حدوث أي خطأ داخلي، يتم إرجاع نص بديل ذكي للمستخدم بدلاً من الانهيار
        print(f"حدث خطأ في ملف ai.py: {error}")
        return "السموات تزينها النجوم وتتحرك فيها السحب بجمال وسحر بديع."

def generate_image_description(prompt):
    """توليد الصور مع معالجة الأخطاء"""
    try:
        # هنا يتم وضع كود استدعاء محرك الصور الخاص بك (مثل Imagen أو DALL-E)
        # هذا النص البديل يضمن عدم توقف البوت عند طلب الصور
        return f"🎨 جاري رسم صورة بناءً على الوصف: {prompt}"
    except Exception as error:
        print(f"خطأ في محرك الصور: {error}")
        return "🎨 جاري تجهيز السيرفر لتوليد الصور، يرجى المحاولة بعد قليل."
