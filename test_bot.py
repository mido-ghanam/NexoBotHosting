#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار وحدات بوت تيليجرام Nexo
"""

import sys
import os

# إضافة مجلد المشروع إلى المسار
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """اختبار استيراد جميع الوحدات"""
    print("🧪 اختبار استيراد الوحدات...")
    
    try:
        from config import config
        print("✅ تم استيراد config بنجاح")
        
        from database import db
        print("✅ تم استيراد database بنجاح")
        
        from api_client import api_client
        print("✅ تم استيراد api_client بنجاح")
        
        from modules.auth import AuthManager
        print("✅ تم استيراد AuthManager بنجاح")
        
        from modules.account import AccountManager
        print("✅ تم استيراد AccountManager بنجاح")
        
        from modules.store import StoreManager
        print("✅ تم استيراد StoreManager بنجاح")
        
        from modules.servers import ServerManager
        print("✅ تم استيراد ServerManager بنجاح")
        
        from modules.support import SupportManager
        print("✅ تم استيراد SupportManager بنجاح")
        
        return True
        
    except ImportError as e:
        print(f"❌ فشل في الاستيراد: {e}")
        return False

def test_database():
    """اختبار قاعدة البيانات"""
    print("\n🗄️ اختبار قاعدة البيانات...")
    
    try:
        from database import db
        
        # اختبار إضافة مستخدم تجريبي
        test_user_id = 123456789
        test_email = "test@example.com"
        test_api_key = "test_api_key_123"
        
        # إضافة المستخدم
        result = db.add_user(test_user_id, test_email, test_api_key)
        if result:
            print("✅ تم إضافة مستخدم تجريبي بنجاح")
        else:
            print("❌ فشل في إضافة المستخدم التجريبي")
            return False
        
        # استرجاع المستخدم
        user = db.get_user(test_user_id)
        if user and user['email'] == test_email:
            print("✅ تم استرجاع بيانات المستخدم بنجاح")
        else:
            print("❌ فشل في استرجاع بيانات المستخدم")
            return False
        
        # اختبار إضافة معاملة
        transaction_result = db.add_transaction(
            test_user_id, 
            'test_transaction', 
            100.0, 
            'معاملة تجريبية'
        )
        if transaction_result:
            print("✅ تم إضافة معاملة تجريبية بنجاح")
        else:
            print("❌ فشل في إضافة المعاملة التجريبية")
            return False
        
        # استرجاع المعاملات
        transactions = db.get_user_transactions(test_user_id)
        if transactions and len(transactions) > 0:
            print("✅ تم استرجاع المعاملات بنجاح")
        else:
            print("❌ فشل في استرجاع المعاملات")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار قاعدة البيانات: {e}")
        return False

def test_config():
    """اختبار الإعدادات"""
    print("\n⚙️ اختبار الإعدادات...")
    
    try:
        from config import config
        
        # التحقق من وجود الإعدادات الأساسية
        if hasattr(config, 'BOT_TOKEN'):
            print("✅ BOT_TOKEN موجود في الإعدادات")
        else:
            print("❌ BOT_TOKEN غير موجود في الإعدادات")
            return False
        
        if hasattr(config, 'CTRLPANEL_BASE_URL'):
            print("✅ CTRLPANEL_BASE_URL موجود في الإعدادات")
        else:
            print("❌ CTRLPANEL_BASE_URL غير موجود في الإعدادات")
            return False
        
        if hasattr(config, 'PTERODACTYL_BASE_URL'):
            print("✅ PTERODACTYL_BASE_URL موجود في الإعدادات")
        else:
            print("❌ PTERODACTYL_BASE_URL غير موجود في الإعدادات")
            return False
        
        if hasattr(config, 'WELCOME_MESSAGE') and config.WELCOME_MESSAGE:
            print("✅ WELCOME_MESSAGE موجود ومُعرَّف")
        else:
            print("❌ WELCOME_MESSAGE غير موجود أو فارغ")
            return False
        
        if hasattr(config, 'HELP_MESSAGE') and config.HELP_MESSAGE:
            print("✅ HELP_MESSAGE موجود ومُعرَّف")
        else:
            print("❌ HELP_MESSAGE غير موجود أو فارغ")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار الإعدادات: {e}")
        return False

def test_api_client():
    """اختبار عميل API"""
    print("\n🌐 اختبار عميل API...")
    
    try:
        from api_client import api_client
        
        # التحقق من وجود الطرق الأساسية
        methods_to_check = [
            'ctrlpanel_login',
            'ctrlpanel_get_user_info',
            'ctrlpanel_get_balance',
            'ctrlpanel_get_products',
            'pterodactyl_get_servers',
            'pterodactyl_get_server_details'
        ]
        
        for method_name in methods_to_check:
            if hasattr(api_client, method_name):
                print(f"✅ طريقة {method_name} موجودة")
            else:
                print(f"❌ طريقة {method_name} غير موجودة")
                return False
        
        # اختبار إنشاء طلب (بدون إرساله فعلياً)
        if hasattr(api_client, '_make_request'):
            print("✅ طريقة _make_request موجودة")
        else:
            print("❌ طريقة _make_request غير موجودة")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار عميل API: {e}")
        return False

def test_bot_structure():
    """اختبار هيكل البوت"""
    print("\n🤖 اختبار هيكل البوت...")
    
    try:
        # محاولة إنشاء البوت (بدون تشغيله)
        import telebot
        
        # اختبار إنشاء بوت وهمي
        fake_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        try:
            test_bot = telebot.TeleBot(fake_token)
            print("✅ تم إنشاء كائن البوت بنجاح")
        except Exception as e:
            print(f"⚠️ تحذير في إنشاء كائن البوت (متوقع مع token وهمي): {e}")
            # إنشاء بوت بدون token للاختبار
            test_bot = telebot.TeleBot("fake_token")
        
        # اختبار إنشاء المديرين
        from modules.auth import AuthManager
        from modules.account import AccountManager
        from modules.store import StoreManager
        from modules.servers import ServerManager
        from modules.support import SupportManager
        
        try:
            auth_manager = AuthManager(test_bot)
            print("✅ تم إنشاء AuthManager بنجاح")
            
            account_manager = AccountManager(test_bot, auth_manager)
            print("✅ تم إنشاء AccountManager بنجاح")
            
            store_manager = StoreManager(test_bot, auth_manager)
            print("✅ تم إنشاء StoreManager بنجاح")
            
            server_manager = ServerManager(test_bot, auth_manager)
            print("✅ تم إنشاء ServerManager بنجاح")
            
            support_manager = SupportManager(test_bot, auth_manager)
            print("✅ تم إنشاء SupportManager بنجاح")
            
        except Exception as e:
            print(f"❌ فشل في إنشاء المديرين: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار هيكل البوت: {e}")
        return False

def main():
    """تشغيل جميع الاختبارات"""
    print("🚀 بدء اختبار بوت تيليجرام Nexo")
    print("=" * 50)
    
    tests = [
        ("استيراد الوحدات", test_imports),
        ("الإعدادات", test_config),
        ("قاعدة البيانات", test_database),
        ("عميل API", test_api_client),
        ("هيكل البوت", test_bot_structure)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 اختبار: {test_name}")
        print("-" * 30)
        
        if test_func():
            passed_tests += 1
            print(f"✅ نجح اختبار {test_name}")
        else:
            print(f"❌ فشل اختبار {test_name}")
    
    print("\n" + "=" * 50)
    print(f"📊 نتائج الاختبارات: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 جميع الاختبارات نجحت! البوت جاهز للتشغيل.")
        return True
    else:
        print("⚠️ بعض الاختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

