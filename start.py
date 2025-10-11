"""
تشغيل البوت والـ Dashboard معاً بدون تعديل أي ملف
"""

import threading
import sys
import os

def run_bot():
    """تشغيل البوت"""
    print("🤖 جاري تشغيل البوت...")
    try:
        # استيراد وتشغيل البوت
        import bot
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")

def run_dashboard():
    """تشغيل الـ Dashboard"""
    print("🌐 جاري تشغيل Dashboard...")
    try:
        # استيراد وتشغيل الـ Dashboard
        import web_dashboard
    except Exception as e:
        print(f"❌ خطأ في تشغيل Dashboard: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 بدء تشغيل جميع الخدمات")
    print("=" * 50)
    
    # إنشاء thread للبوت
    bot_thread = threading.Thread(target=run_bot, daemon=False)
    bot_thread.start()
    
    print("⏳ انتظار 3 ثواني قبل تشغيل Dashboard...")
    import time
    time.sleep(3)
    
    # إنشاء thread للـ Dashboard
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=False)
    dashboard_thread.start()
    
    print("✅ تم تشغيل جميع الخدمات بنجاح!")
    print("=" * 50)
    print("📊 Dashboard: http://0.0.0.0:8080")
    print("🤖 Bot: يعمل في الخلفية")
    print("=" * 50)
    
    # انتظار الـ threads
    bot_thread.join()
    dashboard_thread.join()
