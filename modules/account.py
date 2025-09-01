# -*- coding: utf-8 -*-
"""
وحدة إدارة الحساب والرصيد
"""

import telebot
from telebot import types
from database import db
from api_client import api_client
from datetime import datetime

class AccountManager:
    def __init__(self, bot: telebot.TeleBot, auth_manager):
        self.bot = bot
        self.auth = auth_manager
        self.user_states = {}
    
    def register_handlers(self):
        """تسجيل معالجات الأوامر"""
        self.bot.message_handler(commands=['account'])(self.handle_account_command)
        self.bot.message_handler(commands=['balance'])(self.handle_balance_command)
        self.bot.message_handler(commands=['coupon'])(self.handle_coupon_command)
        self.bot.message_handler(func=lambda message: self.is_waiting_for_coupon(message))(self.handle_coupon_input)
    
    def is_waiting_for_coupon(self, message):
        """التحقق من أن المستخدم في حالة انتظار إدخال كوبون"""
        return (message.from_user.id in self.user_states and 
                self.user_states[message.from_user.id].get('step') == 'waiting_coupon')
    
    @property
    def require_login(self):
        """ديكوريتر للتحقق من تسجيل الدخول"""
        return self.auth.require_login
    
    def handle_account_command(self, message):
        """معالج أمر عرض بيانات الحساب"""
        @self.require_login
        def _handle_account(msg):
            user_id = msg.from_user.id
            api_key = self.auth.get_user_api_key(user_id)
            
            if not api_key:
                self.bot.reply_to(msg, "❌ لم يتم العثور على مفتاح API. قم بتسجيل الدخول مرة أخرى.")
                return
            
            # الحصول على معلومات المستخدم
            user_info = api_client.ctrlpanel_get_user_info(api_key)
            balance_info = api_client.ctrlpanel_get_balance(api_key)
            
            if not user_info or not user_info.get('success'):
                self.bot.reply_to(msg, "❌ فشل في الحصول على بيانات الحساب. تحقق من الاتصال.")
                return
            
            user_data = user_info.get('data', {})
            balance = balance_info.get('data', {}).get('balance', 0) if balance_info else 0
            
            # إنشاء رسالة بيانات الحساب
            account_text = f"""
👤 **بيانات الحساب**

📧 **البريد الإلكتروني:** `{user_data.get('email', 'غير محدد')}`
💰 **الرصيد:** `{balance:.2f}` كوين
🆔 **معرف المستخدم:** `{user_data.get('id', 'غير محدد')}`
📅 **تاريخ التسجيل:** `{user_data.get('created_at', 'غير محدد')}`
🕐 **آخر نشاط:** `{datetime.now().strftime('%Y-%m-%d %H:%M')}`

📊 **إحصائيات سريعة:**
🖥️ السيرفرات النشطة: `{len(db.get_user_servers(user_id))}`
💳 المعاملات الأخيرة: `{len(db.get_user_transactions(user_id, 5))}`
            """
            
            # إنشاء الأزرار التفاعلية
            markup = types.InlineKeyboardMarkup()
            balance_btn = types.InlineKeyboardButton("💰 عرض الرصيد", callback_data="show_balance")
            transactions_btn = types.InlineKeyboardButton("📜 المعاملات الأخيرة", callback_data="show_transactions")
            referral_btn = types.InlineKeyboardButton("👥 نظام الإحالة", callback_data="show_referral")
            
            markup.add(balance_btn)
            markup.add(transactions_btn)
            markup.add(referral_btn)
            
            self.bot.reply_to(msg, account_text, reply_markup=markup, parse_mode='Markdown')
        
        _handle_account(message)
    
    def handle_balance_command(self, message):
        """معالج أمر عرض الرصيد"""
        @self.require_login
        def _handle_balance(msg):
            user_id = msg.from_user.id
            api_key = self.auth.get_user_api_key(user_id)
            
            if not api_key:
                self.bot.reply_to(msg, "❌ لم يتم العثور على مفتاح API.")
                return
            
            # الحصول على معلومات الرصيد
            balance_info = api_client.ctrlpanel_get_balance(api_key)
            
            if not balance_info or not balance_info.get('success'):
                self.bot.reply_to(msg, "❌ فشل في الحصول على بيانات الرصيد.")
                return
            
            balance_data = balance_info.get('data', {})
            current_balance = balance_data.get('balance', 0)
            
            # الحصول على المعاملات الأخيرة
            recent_transactions = db.get_user_transactions(user_id, 5)
            
            balance_text = f"""
💰 **رصيد المحفظة**

💎 **الرصيد الحالي:** `{current_balance:.2f}` كوين

📊 **المعاملات الأخيرة:**
            """
            
            if recent_transactions:
                for trans in recent_transactions:
                    trans_type = "➕" if trans['amount'] > 0 else "➖"
                    balance_text += f"\n{trans_type} `{abs(trans['amount']):.2f}` - {trans['description']}"
            else:
                balance_text += "\n📝 لا توجد معاملات حديثة"
            
            # إنشاء الأزرار
            markup = types.InlineKeyboardMarkup()
            coupon_btn = types.InlineKeyboardButton("🎫 تفعيل كوبون", callback_data="redeem_coupon")
            history_btn = types.InlineKeyboardButton("📜 سجل المعاملات", callback_data="transaction_history")
            
            markup.add(coupon_btn)
            markup.add(history_btn)
            
            self.bot.reply_to(msg, balance_text, reply_markup=markup, parse_mode='Markdown')
        
        _handle_balance(message)
    
    def handle_coupon_command(self, message):
        """معالج أمر تفعيل الكوبون"""
        @self.require_login
        def _handle_coupon(msg):
            user_id = msg.from_user.id
            self.user_states[user_id] = {'step': 'waiting_coupon'}
            
            self.bot.reply_to(msg, 
                             "🎫 **تفعيل كوبون الشحن**\n\n"
                             "أدخل رمز الكوبون:",
                             parse_mode='Markdown')
        
        _handle_coupon(message)
    
    def handle_coupon_input(self, message):
        """معالج إدخال رمز الكوبون"""
        user_id = message.from_user.id
        coupon_code = message.text.strip()
        
        # إزالة المستخدم من حالة الانتظار
        if user_id in self.user_states:
            del self.user_states[user_id]
        
        api_key = self.auth.get_user_api_key(user_id)
        if not api_key:
            self.bot.reply_to(message, "❌ لم يتم العثور على مفتاح API.")
            return
        
        # محاولة تفعيل الكوبون
        result = api_client.ctrlpanel_redeem_coupon(api_key, coupon_code)
        
        if result and result.get('success'):
            amount = result.get('data', {}).get('amount', 0)
            new_balance = result.get('data', {}).get('new_balance', 0)
            
            # حفظ المعاملة في قاعدة البيانات
            db.add_transaction(user_id, 'coupon_redeem', amount, f'تفعيل كوبون: {coupon_code}')
            
            success_text = f"""
✅ **تم تفعيل الكوبون بنجاح!**

🎫 **رمز الكوبون:** `{coupon_code}`
💎 **المبلغ المضاف:** `{amount:.2f}` كوين
💰 **الرصيد الجديد:** `{new_balance:.2f}` كوين

شكراً لاستخدامك منصة Nexo! 🎉
            """
            
            self.bot.reply_to(message, success_text, parse_mode='Markdown')
        else:
            error_msg = result.get('message', 'كوبون غير صحيح أو منتهي الصلاحية') if result else 'فشل في الاتصال بالخادم'
            self.bot.reply_to(message, f"❌ فشل في تفعيل الكوبون: {error_msg}")
    
    def handle_callback_query(self, call):
        """معالج الأزرار التفاعلية"""
        user_id = call.from_user.id
        
        if call.data == "show_balance":
            # عرض تفاصيل الرصيد
            api_key = self.auth.get_user_api_key(user_id)
            balance_info = api_client.ctrlpanel_get_balance(api_key)
            
            if balance_info and balance_info.get('success'):
                balance = balance_info.get('data', {}).get('balance', 0)
                self.bot.answer_callback_query(call.id, f"رصيدك الحالي: {balance:.2f} كوين")
            else:
                self.bot.answer_callback_query(call.id, "فشل في الحصول على الرصيد")
        
        elif call.data == "show_transactions":
            # عرض المعاملات الأخيرة
            transactions = db.get_user_transactions(user_id, 10)
            
            if transactions:
                trans_text = "📜 **المعاملات الأخيرة:**\n\n"
                for trans in transactions:
                    trans_type = "➕" if trans['amount'] > 0 else "➖"
                    date = trans['created_at'][:10]  # تاريخ فقط
                    trans_text += f"{trans_type} `{abs(trans['amount']):.2f}` - {trans['description']} ({date})\n"
                
                self.bot.edit_message_text(
                    trans_text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
            else:
                self.bot.answer_callback_query(call.id, "لا توجد معاملات")
        
        elif call.data == "show_referral":
            # عرض معلومات نظام الإحالة
            api_key = self.auth.get_user_api_key(user_id)
            referral_info = api_client.ctrlpanel_get_referral_info(api_key)
            
            if referral_info and referral_info.get('success'):
                ref_data = referral_info.get('data', {})
                ref_link = ref_data.get('referral_link', 'غير متوفر')
                ref_count = ref_data.get('referral_count', 0)
                ref_earnings = ref_data.get('referral_earnings', 0)
                
                referral_text = f"""
👥 **نظام الإحالة**

🔗 **رابط الإحالة:**
`{ref_link}`

📊 **الإحصائيات:**
👤 عدد المسجلين: `{ref_count}`
💰 الأرباح: `{ref_earnings:.2f}` كوين

💡 **كيفية الاستخدام:**
شارك رابط الإحالة مع أصدقائك واحصل على مكافآت عند تسجيلهم!
                """
                
                self.bot.edit_message_text(
                    referral_text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
            else:
                self.bot.answer_callback_query(call.id, "فشل في الحصول على معلومات الإحالة")
        
        elif call.data == "redeem_coupon":
            # بدء عملية تفعيل كوبون
            self.user_states[user_id] = {'step': 'waiting_coupon'}
            self.bot.edit_message_text(
                "🎫 **تفعيل كوبون الشحن**\n\nأدخل رمز الكوبون:",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
        
        elif call.data == "transaction_history":
            # عرض سجل المعاملات الكامل
            transactions = db.get_user_transactions(user_id, 20)
            
            if transactions:
                trans_text = "📜 **سجل المعاملات الكامل:**\n\n"
                for trans in transactions:
                    trans_type = "➕" if trans['amount'] > 0 else "➖"
                    date_time = trans['created_at'][:16].replace('T', ' ')
                    trans_text += f"{trans_type} `{abs(trans['amount']):.2f}` - {trans['description']}\n📅 {date_time}\n\n"
                
                # تقسيم الرسالة إذا كانت طويلة
                if len(trans_text) > 4000:
                    trans_text = trans_text[:3900] + "\n\n... والمزيد"
                
                self.bot.edit_message_text(
                    trans_text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
            else:
                self.bot.answer_callback_query(call.id, "لا توجد معاملات")

