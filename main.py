#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت تيليجرام لإدارة منصة Nexo
"""

import telebot
from telebot import types
import logging
import sys
import os

# إضافة مجلد المشروع إلى المسار
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# استيراد الوحدات
from config import config
from database import db
from modules.auth import AuthManager
from modules.account import AccountManager
from modules.store import StoreManager
from modules.servers import ServerManager
from modules.support import SupportManager

# إعداد السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class NexoTelegramBot:
    def __init__(self):
        """تهيئة البوت"""
        if not config.BOT_TOKEN or config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            logger.error("❌ لم يتم تعيين BOT_TOKEN في متغيرات البيئة!")
            sys.exit(1)
        
        # إنشاء البوت
        self.bot = telebot.TeleBot(config.BOT_TOKEN)
        
        # إنشاء مديري الوحدات
        self.auth_manager = AuthManager(self.bot)
        self.account_manager = AccountManager(self.bot, self.auth_manager)
        self.store_manager = StoreManager(self.bot, self.auth_manager)
        self.server_manager = ServerManager(self.bot, self.auth_manager)
        self.support_manager = SupportManager(self.bot, self.auth_manager)
        
        # تسجيل المعالجات
        self.register_handlers()
        
        logger.info("✅ تم تهيئة البوت بنجاح!")
    
    def register_handlers(self):
        """تسجيل جميع معالجات الأوامر"""
        
        # الأوامر الأساسية
        self.bot.message_handler(commands=['start'])(self.handle_start_command)
        self.bot.message_handler(commands=['help'])(self.handle_help_command)
        
        # تسجيل معالجات الوحدات
        self.auth_manager.register_handlers()
        self.account_manager.register_handlers()
        self.store_manager.register_handlers()
        self.server_manager.register_handlers()
        self.support_manager.register_handlers()
        
        # معالج الأزرار التفاعلية
        self.bot.callback_query_handler(func=lambda call: True)(self.handle_callback_query)
        
        # معالج الرسائل غير المعروفة
        self.bot.message_handler(func=lambda message: True)(self.handle_unknown_message)
    
    def handle_start_command(self, message):
        """معالج أمر البدء"""
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "المستخدم"
        
        # إنشاء الأزرار الرئيسية
        markup = types.InlineKeyboardMarkup()
        login_btn = types.InlineKeyboardButton("🔐 تسجيل الدخول", callback_data="quick_login")
        help_btn = types.InlineKeyboardButton("ℹ️ المساعدة", callback_data="show_help")
        
        markup.add(login_btn)
        markup.add(help_btn)
        
        welcome_text = f"""
👋 **مرحباً {username}!**

{config.WELCOME_MESSAGE}

🚀 **ابدأ الآن:**
        """
        
        self.bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode='Markdown')
        
        logger.info(f"مستخدم جديد بدأ البوت: {user_id} ({username})")
    
    def handle_help_command(self, message):
        """معالج أمر المساعدة"""
        self.bot.reply_to(message, config.HELP_MESSAGE, parse_mode='Markdown')
    
    def handle_callback_query(self, call):
        """معالج الأزرار التفاعلية الرئيسية"""
        try:
            # توزيع الاستعلامات على الوحدات المناسبة
            if call.data.startswith(("login_", "quick_login")):
                if call.data == "quick_login":
                    call.data = "login_email"  # تحويل إلى تسجيل دخول بالإيميل
                self.auth_manager.handle_callback_query(call)
            
            elif call.data.startswith(("show_balance", "show_transactions", "show_referral", 
                                     "redeem_coupon", "transaction_history")):
                self.account_manager.handle_callback_query(call)
            
            elif call.data.startswith(("store_page_", "buy_product_", "refresh_store")):
                self.store_manager.handle_callback_query(call)
            
            elif call.data.startswith(("servers_page_", "manage_server_", "power_", 
                                     "show_logs_", "show_console_", "back_to_servers", 
                                     "refresh_servers")):
                self.server_manager.handle_callback_query(call)
            
            elif call.data.startswith(("tickets_page_", "view_ticket_", "create_new_ticket", 
                                     "priority_", "reply_ticket_", "back_to_tickets", 
                                     "refresh_tickets")):
                self.support_manager.handle_callback_query(call)
            
            elif call.data == "show_help":
                self.bot.edit_message_text(
                    config.HELP_MESSAGE,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
            
            else:
                self.bot.answer_callback_query(call.id, "❌ أمر غير معروف")
        
        except Exception as e:
            logger.error(f"خطأ في معالجة الاستعلام: {e}")
            self.bot.answer_callback_query(call.id, "❌ حدث خطأ، حاول مرة أخرى")
    
    def handle_unknown_message(self, message):
        """معالج الرسائل غير المعروفة"""
        # تجاهل الرسائل التي يتم معالجتها بواسطة الوحدات الأخرى
        if (self.auth_manager.is_waiting_for_credentials(message) or
            self.account_manager.is_waiting_for_coupon(message) or
            self.store_manager.is_waiting_for_purchase_input(message) or
            self.server_manager.is_waiting_for_server_input(message) or
            self.support_manager.is_waiting_for_ticket_input(message)):
            return
        
        # رسالة للأوامر غير المعروفة
        unknown_text = """
❓ **أمر غير معروف**

استخدم /help لعرض قائمة الأوامر المتاحة.

🔗 **الأوامر السريعة:**
/login - تسجيل الدخول
/account - بيانات الحساب
/store - المتجر
/servers - السيرفرات
/support - الدعم الفني
        """
        
        self.bot.reply_to(message, unknown_text, parse_mode='Markdown')
    
    def run(self):
        """تشغيل البوت"""
        logger.info("🚀 بدء تشغيل بوت Nexo...")
        
        try:
            # تشغيل البوت
            self.bot.infinity_polling(none_stop=True, interval=1)
            
        except KeyboardInterrupt:
            logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        finally:
            logger.info("👋 تم إغلاق البوت")

def main():
    """الدالة الرئيسية"""
    print("""
    ╔══════════════════════════════════════╗
    ║           بوت تيليجرام Nexo          ║
    ║        إدارة شاملة لمنصتك           ║
    ╚══════════════════════════════════════╝
    """)
    
    try:
        # إنشاء وتشغيل البوت
        bot = NexoTelegramBot()
        bot.run()
        
    except Exception as e:
        logger.error(f"❌ فشل في تشغيل البوت: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

