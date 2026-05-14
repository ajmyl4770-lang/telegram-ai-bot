# مصفوفة تخزين السجل التاريخي في الذاكرة لتفادي انهيار البوت
_chat_history_db = {}

def get_user_history(user_id):
    """قراءة مصفوفة السجل التاريخي للمستخدم بأمان"""
    if user_id not in _chat_history_db:
        _chat_history_db[user_id] = []
    return _chat_history_db[user_id]

def save_to_history(user_id, role, content):
    """إصلاح وحفظ البيانات في السجل مع تصفية رسائل الأخطاء"""
    # منع دخول رسائل الأخطاء والرموز التحذيرية إلى الذاكرة التاريخية
    if not content or "⚠️" in content or "فشل" in content:
        return
        
    history = get_user_history(user_id)
    
    # تنسيق المصفوفة البرمجية بشكل صحيح ومقبول للمحرك
    history.append({
        "role": role,
        "parts": [str(content)]
    })
    
    # تحديث مصفوفة قاعدة البيانات
    _chat_history_db[user_id] = history

def clear_user_history(user_id):
    """تفريغ السجل في حال رغبت في بدء جلسة جديدة نظيفة"""
    if user_id in _chat_history_db:
        _chat_history_db[user_id] = []
