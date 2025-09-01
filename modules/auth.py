# -*- coding: utf-8 -*-
"""
وحدة المصادقة وتسجيل الدخول/الخروج
"""

import telebot
from telebot import types
from database import db
from api_client import api_client
from config import config

class AuthManager:
    def __init__(self, bot: telebot.TeleBot):
        self.bot = bot
        self.user_states = {}  # لتتبع حالة المستخدمين أثناء تسجيل الدخول
    
    def register_handlers(self):
        """تسجيل معالجات الأوامر"""
        self.bot.message_handler(commands=['login'])(self.handle_login_command)
        self.bot.message_handler(commands=['logout'])(self.handle_logout_command)
        self.bot.message_handler(func=lambda message: self.is_waiting_for_credentials(message))(self.handle_credentials_input)
    
    def is_waiting_for_credentials(self, message):
        """التحقق من أن المستخدم في حالة انتظار إدخال بيانات الدخول"""
        return message.from_user.id in self.user_states
    
    def handle_login_command(self, message):
        """معالج أمر تسجيل الدخول"""
        user_id = message.from_user.id
        
        # التحقق من حالة تسجيل الدخول الحالية
        user = db.get_user(user_id)
        if user and user.get('is_logged_in'):
            self.bot.reply_to(message, "✅ أنت مسجل دخول بالفعل!\n\nاستخدم /account لعرض بيانات حسابك.")
            return
        
        # بدء عملية تسجيل الدخول
        markup = types.InlineKeyboardMarkup()
        email_btn = types.InlineKeyboardButton("📧 تسجيل الدخول بالإيميل", callback_data="login_email")
        api_btn = types.InlineKeyboardButton("🔑 تسجيل الدخول بـ API Key", callback_data="login_api")
        markup.add(email_btn)
        markup.add(api_btn)
        
        self.bot.reply_to(message, 
                         "🔐 **تسجيل الدخول إلى منصة Nexo**\n\n"
                         "اختر طريقة تسجيل الدخول:",
                         reply_markup=markup, parse_mode='Markdown')
    
    def handle_logout_command(self, message):
        """معالج أمر تسجيل الخروج"""
        user_id = message.from_user.id
        
        # التحقق من حالة تسجيل الدخول
        user = db.get_user(user_id)
        if not user or not user.get('is_logged_in'):
            self.bot.reply_to(message, "❌ أنت غير مسجل دخول!")
            return
        
        # تسجيل الخروج
        if db.update_user_login_status(user_id, False):
            self.bot.reply_to(message, "✅ تم تسجيل الخروج بنجاح!\n\nاستخدم /login لتسجيل الدخول مرة أخرى.")
        else:
            self.bot.reply_to(message, "❌ حدث خطأ أثناء تسجيل الخروج. حاول مرة أخرى.")
    
    def handle_credentials_input(self, message):
        """معالج إدخال بيانات الدخول"""
        user_id = message.from_user.id
        
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        
        if state['step'] == 'waiting_email':
            # حفظ الإيميل والانتقال لكلمة المرور
            state['email'] = message.text.strip()
            state['step'] = 'waiting_password'
            self.bot.reply_to(message, "🔒 الآن أدخل كلمة المرور:")
            
        elif state['step'] == 'waiting_password':
            # محاولة تسجيل الدخول
            password = message.text.strip()
            self.attempt_email_login(message, state['email'], password)
            
        elif state['step'] == 'waiting_api_key':
            # محاولة تسجيل الدخول بـ API Key
            api_key = message.text.strip()
            self.attempt_api_login(message, api_key)
    
    def attempt_email_login(self, message, email, password):
        """محاولة تسجيل الدخول بالإيميل وكلمة المرور"""
        user_id = message.from_user.id
        
        # إزالة المستخدم من حالة الانتظار
        if user_id in self.user_states:
            del self.user_states[user_id]
        
        # محاولة تسجيل الدخول عبر API
        login_result = api_client.ctrlpanel_login(email, password)
        
        if login_result and login_result.get('success'):
            api_key = login_result.get('api_key') or login_result.get('token')
            
            if api_key:
                # حفظ بيانات المستخدم في قاعدة البيانات
                if db.add_user(user_id, email, api_key):
                    self.bot.reply_to(message, 
                                     f"✅ **تم تسجيل الدخول بنجاح!**\n\n"
                                     f"📧 الإيميل: `{email}`\n"
                                     f"🕐 وقت الدخول: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                                     f"استخدم /account لعرض بيانات حسابك.",
                                     parse_mode='Markdown')
                else:
                    self.bot.reply_to(message, "❌ حدث خطأ في حفظ بيانات الدخول. حاول مرة أخرى.")
            else:
                self.bot.reply_to(message, "❌ لم يتم الحصول على مفتاح API. تحقق من بيانات الدخول.")
        else:
            error_msg = login_result.get('message', 'بيانات دخول غير صحيحة') if login_result else 'فشل في الاتصال بالخادم'
            self.bot.reply_to(message, f"❌ فشل تسجيل الدخول: {error_msg}")
    
    def attempt_api_login(self, message, api_key):
        """محاولة تسجيل الدخول بـ API Key"""
        user_id = message.from_user.id
        
        # إزالة المستخدم من حالة الانتظار
        if user_id in self.user_states:
            del self.user_states[user_id]
        
        # التحقق من صحة API Key
        user_info = api_client.ctrlpanel_get_user_info(api_key)
        
        if user_info and user_info.get('success'):
            email = user_info.get('data', {}).get('email', 'غير محدد')
            
            # حفظ بيانات المستخدم
            if db.add_user(user_id, email, api_key):
                self.bot.reply_to(message, 
                                 f"✅ **تم تسجيل الدخول بنجاح!**\n\n"
                                 f"📧 الإيميل: `{email}`\n"
                                 f"🔑 تم استخدام API Key\n"
                                 f"🕐 وقت الدخول: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                                 f"استخدم /account لعرض بيانات حسابك.",
                                 parse_mode='Markdown')
            else:
                self.bot.reply_to(message, "❌ حدث خطأ في حفظ بيانات الدخول. حاول مرة أخرى.")
        else:
            self.bot.reply_to(message, "❌ API Key غير صحيح أو منتهي الصلاحية.")
    
    def handle_callback_query(self, call):
        """معالج الأزرار التفاعلية"""
        if call.data == "login_email":
            self.user_states[call.from_user.id] = {'step': 'waiting_email'}
            self.bot.edit_message_text(
                "📧 **تسجيل الدخول بالإيميل**\n\nأدخل عنوان البريد الإلكتروني:",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
            
        elif call.data == "login_api":
            self.user_states[call.from_user.id] = {'step': 'waiting_api_key'}
            self.bot.edit_message_text(
                "🔑 **تسجيل الدخول بـ API Key**\n\n"
                "أدخل مفتاح API الخاص بك:\n"
                "(يمكنك الحصول عليه من لوحة التحكم)",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
    
    def is_user_logged_in(self, user_id: int) -> bool:
        """التحقق من حالة تسجيل دخول المستخدم"""
        user = db.get_user(user_id)
        return user and user.get('is_logged_in', False)
    
    def get_user_api_key(self, user_id: int) -> str:
        """الحصول على API Key للمستخدم"""
        user = db.get_user(user_id)
        return user.get('api_key') if user else None
    
    def require_login(self, func):
        """ديكوريتر للتحقق من تسجيل الدخول قبل تنفيذ الدالة"""
        def wrapper(message):
            if not self.is_user_logged_in(message.from_user.id):
                self.bot.reply_to(message, 
                                 "🔐 يجب تسجيل الدخول أولاً!\n\n"
                                 "استخدم /login لتسجيل الدخول.")
                return
            return func(message)
        return wrapper

from datetime import datetime

