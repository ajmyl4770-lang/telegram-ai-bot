import ai
import database

def handle_user_request(user_id, request_type, user_input):
    """المحرك الرئيسي لإدارة طلبات أبو جميل الأشول"""
    
    if request_type == "توليد صورة":
        print(f"🎨 طلب رسم: {user_input}")
        # استدعاء محرك الصور مباشرة
        image_result = ai.generate_image_description(user_input)
        return image_result
        
    else:
        return "الرجاء اختيار خدمة صحيحة (توليد صورة)."

# لتجربة التشغيل الفوري للملف بعد التعديل
if __name__ == "__main__":
    print("--- تجربة نظام مركز بن علي للذكاء الصناعي ---")
    # تجربة طلب رسم قط لابس نظارة
    نتيجة_الصورة = handle_user_request("user_123", "توليد صورة", "قط لابس نظارة")
    print(نتيجة_الصورة)
