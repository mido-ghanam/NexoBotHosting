# -*- coding: utf-8 -*-
"""
إعدادات بوت تيليجرام لمنصة Nexo
"""

import os
from dataclasses import dataclass, field

@dataclass
class Config:
    # إعدادات البوت
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    
    # إعدادات CtrlPanel API
    CTRLPANEL_BASE_URL: str = os.getenv('CTRLPANEL_BASE_URL', 'https://nexo.midoghanam.site')
    CTRLPANEL_API_URL: str = field(init=False)
    
    # إعدادات Pterodactyl API
    PTERODACTYL_BASE_URL: str = os.getenv('PTERODACTYL_BASE_URL', 'https://panal.nexo.midoghanam.site')
    PTERODACTYL_API_URL: str = field(init=False)
    
    # إعدادات قاعدة البيانات
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'bot_database.db')
    
    # إعدادات عامة
    ADMIN_USER_IDS: list = field(default_factory=lambda: [123456789])  # ضع معرف المستخدم الخاص بك هنا
    MAX_SERVERS_PER_USER: int = 10
    DEFAULT_LANGUAGE: str = 'ar'
    
    def __post_init__(self):
        self.CTRLPANEL_API_URL = f"{self.CTRLPANEL_BASE_URL}/api"
        self.PTERODACTYL_API_URL = f"{self.PTERODACTYL_BASE_URL}/api"
    
    # رسائل البوت
    WELCOME_MESSAGE: str = """
🎉 مرحباً بك في بوت إدارة منصة Nexo!

يمكنك من خلال هذا البوت:
• إدارة حسابك ورصيدك
• عرض وشراء المنتجات من المتجر
• إدارة السيرفرات الخاصة بك
• فتح تذاكر الدعم الفني
• استخدام نظام الإحالة

للبدء، استخدم الأوامر التالية:
/login - تسجيل الدخول
/help - عرض جميع الأوامر المتاحة
    """
    
    HELP_MESSAGE: str = """
📋 قائمة الأوامر المتاحة:

🔐 إدارة الحساب:
/login - تسجيل الدخول
/logout - تسجيل الخروج
/account - عرض بيانات الحساب

💰 المحفظة والرصيد:
/balance - عرض الرصيد
/coupon - تفعيل كوبون شحن

🛒 المتجر:
/store - عرض المنتجات
/buy - شراء منتج

🖥️ السيرفرات:
/servers - عرض السيرفرات
/server - إدارة سيرفر محدد

🎫 الدعم الفني:
/support - عرض التذاكر
/ticket - فتح تذكرة جديدة

👥 نظام الإحالة:
/referral - عرض رابط الإحالة

ℹ️ أخرى:
/help - عرض هذه القائمة
    """

# إنشاء كائن الإعدادات
config = Config()

