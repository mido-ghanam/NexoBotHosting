#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت تشغيل بوت تيليجرام Nexo مع معالجة الأخطاء
"""

import os
import sys

def check_environment():
    """التحقق من متغيرات البيئة المطلوبة"""
    print("🔍 التحقق من متغيرات البيئة...")
    
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
        print("❌ لم يتم تعيين BOT_TOKEN!")
        print("💡 يرجى تعيين متغير البيئة BOT_TOKEN أو إنشاء ملف .env")
        print("📝 مثال: export BOT_TOKEN='your_bot_token_here'")
        return False
    
    print(f"✅ BOT_TOKEN موجود: {bot_token[:10]}...")
    
    # التحقق من المتغيرات الأخرى (اختيارية)
    ctrlpanel_url = os.getenv('CTRLPANEL_BASE_URL', 'https://nexo.midoghanam.site')
    pterodactyl_url = os.getenv('PTERODACTYL_BASE_URL', 'https://panal.nexo.midoghanam.site')
    
    print(f"✅ CTRLPANEL_BASE_URL: {ctrlpanel_url}")
    print(f"✅ PTERODACTYL_BASE_URL: {pterodactyl_url}")
    
    return True

def load_env_file():
    """تحميل ملف .env إذا كان موجوداً"""
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"📁 تم العثور على ملف {env_file}, جاري التحميل...")
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            print("✅ تم تحميل متغيرات البيئة من .env")
        except Exception as e:
            print(f"⚠️ تحذير: فشل في تحميل ملف .env: {e}")
    else:
        print(f"📝 لم يتم العثور على ملف {env_file}")

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    print("""
    ╔══════════════════════════════════════╗
    ║           بوت تيليجرام Nexo          ║
    ║        إدارة شاملة لمنصتك           ║
    ╚══════════════════════════════════════╝
    """)
    
    # تحميل متغيرات البيئة
    load_env_file()
    
    # التحقق من البيئة
    if not check_environment():
        print("\n❌ فشل في التحقق من البيئة. يرجى إصلاح المشاكل أعلاه.")
        sys.exit(1)
    
    print("\n🚀 بدء تشغيل البوت...")
    
    try:
        # استيراد وتشغيل البوت
        from main import NexoTelegramBot
        
        bot = NexoTelegramBot()
        print("✅ تم تهيئة البوت بنجاح!")
        print("🔄 البوت يعمل الآن... اضغط Ctrl+C للإيقاف")
        
        bot.run()
        
    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف البوت بواسطة المستخدم")
        sys.exit(0)
    except ImportError as e:
        print(f"\n❌ خطأ في الاستيراد: {e}")
        print("💡 تأكد من تثبيت جميع المتطلبات: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل البوت: {e}")
        print("📋 راجع ملف bot.log للمزيد من التفاصيل")
        sys.exit(1)

if __name__ == "__main__":
    main()

