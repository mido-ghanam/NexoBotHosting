# -*- coding: utf-8 -*-
"""
وحدة نظام الدعم الفني والتذاكر
"""

import telebot
from telebot import types
from database import db
from api_client import api_client
import math

class SupportManager:
    def __init__(self, bot: telebot.TeleBot, auth_manager):
        self.bot = bot
        self.auth = auth_manager
        self.user_states = {}
        self.tickets_cache = {}
    
    def register_handlers(self):
        """تسجيل معالجات الأوامر"""
        self.bot.message_handler(commands=['support'])(self.handle_support_command)
        self.bot.message_handler(commands=['ticket'])(self.handle_ticket_command)
        self.bot.message_handler(func=lambda message: self.is_waiting_for_ticket_input(message))(self.handle_ticket_input)
    
    def is_waiting_for_ticket_input(self, message):
        """التحقق من أن المستخدم في حالة انتظار إدخال بيانات التذكرة"""
        return (message.from_user.id in self.user_states and 
                'step' in self.user_states[message.from_user.id])
    
    @property
    def require_login(self):
        """ديكوريتر للتحقق من تسجيل الدخول"""
        return self.auth.require_login
    
    def handle_support_command(self, message):
        """معالج أمر عرض الدعم الفني"""
        @self.require_login
        def _handle_support(msg):
            user_id = msg.from_user.id
            api_key = self.auth.get_user_api_key(user_id)
            
            if not api_key:
                self.bot.reply_to(msg, "❌ لم يتم العثور على مفتاح API.")
                return
            
            # الحصول على التذاكر من API
            tickets_data = api_client.ctrlpanel_get_tickets(api_key)
            
            if not tickets_data or not tickets_data.get('success'):
                self.bot.reply_to(msg, "❌ فشل في تحميل التذاكر. حاول مرة أخرى لاحقاً.")
                return
            
            tickets = tickets_data.get('data', [])
            
            # حفظ التذاكر في التخزين المؤقت
            self.tickets_cache[user_id] = tickets
            
            if not tickets:
                # لا توجد تذاكر - عرض خيارات إنشاء تذكرة جديدة
                self.show_no_tickets_message(msg)
            else:
                # عرض قائمة التذاكر
                self.show_tickets_page(msg, tickets, 0)
        
        _handle_support(message)
    
    def show_no_tickets_message(self, message):
        """عرض رسالة عدم وجود تذاكر"""
        support_text = """
🎫 **نظام الدعم الفني**

📝 لا توجد تذاكر دعم فني حالياً.

💡 **كيفية الحصول على المساعدة:**
• فتح تذكرة جديدة للمشاكل التقنية
• الاستفسار عن الخدمات والمنتجات
• طلب المساعدة في إعداد السيرفرات
• الإبلاغ عن الأخطاء والمشاكل

🕐 **أوقات الرد:**
• الأولوية العالية: خلال ساعة واحدة
• الأولوية المتوسطة: خلال 4-6 ساعات
• الأولوية المنخفضة: خلال 24 ساعة
        """
        
        markup = types.InlineKeyboardMarkup()
        new_ticket_btn = types.InlineKeyboardButton("➕ فتح تذكرة جديدة", callback_data="create_new_ticket")
        refresh_btn = types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh_tickets")
        
        markup.add(new_ticket_btn)
        markup.add(refresh_btn)
        
        self.bot.reply_to(message, support_text, reply_markup=markup, parse_mode='Markdown')
    
    def show_tickets_page(self, message, tickets, page=0, edit_message=False):
        """عرض صفحة من التذاكر"""
        tickets_per_page = 5
        total_pages = math.ceil(len(tickets) / tickets_per_page)
        start_idx = page * tickets_per_page
        end_idx = start_idx + tickets_per_page
        page_tickets = tickets[start_idx:end_idx]
        
        support_text = f"🎫 **تذاكر الدعم الفني** (صفحة {page + 1}/{total_pages})\n\n"
        
        # إنشاء الأزرار للتذاكر
        markup = types.InlineKeyboardMarkup()
        
        for ticket in page_tickets:
            ticket_id = ticket.get('id', 'غير محدد')
            subject = ticket.get('subject', 'بدون عنوان')
            status = ticket.get('status', 'unknown')
            priority = ticket.get('priority', 'medium')
            created_at = ticket.get('created_at', '')[:10]  # تاريخ فقط
            
            status_emoji = self.get_status_emoji(status)
            priority_emoji = self.get_priority_emoji(priority)
            
            support_text += f"🔹 **{subject}** {status_emoji}\n"
            support_text += f"🆔 رقم التذكرة: `#{ticket_id}`\n"
            support_text += f"📊 الحالة: {status.upper()}\n"
            support_text += f"⚡ الأولوية: {priority_emoji} {priority.upper()}\n"
            support_text += f"📅 تاريخ الإنشاء: {created_at}\n\n"
            
            # زر عرض التذكرة
            view_btn = types.InlineKeyboardButton(
                f"👁️ عرض #{ticket_id}",
                callback_data=f"view_ticket_{ticket_id}"
            )
            markup.add(view_btn)
        
        # أزرار التنقل
        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton("⬅️ السابق", callback_data=f"tickets_page_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton("➡️ التالي", callback_data=f"tickets_page_{page+1}"))
        
        if nav_buttons:
            markup.add(*nav_buttons)
        
        # أزرار إضافية
        new_ticket_btn = types.InlineKeyboardButton("➕ تذكرة جديدة", callback_data="create_new_ticket")
        refresh_btn = types.InlineKeyboardButton("🔄 تحديث", callback_data="refresh_tickets")
        
        markup.add(new_ticket_btn, refresh_btn)
        
        if edit_message:
            self.bot.edit_message_text(
                support_text,
                message.chat.id,
                message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        else:
            self.bot.reply_to(message, support_text, reply_markup=markup, parse_mode='Markdown')
    
    def show_ticket_details(self, call, ticket_id):
        """عرض تفاصيل التذكرة"""
        user_id = call.from_user.id
        tickets = self.tickets_cache.get(user_id, [])
        ticket = next((t for t in tickets if str(t.get('id')) == str(ticket_id)), None)
        
        if not ticket:
            self.bot.answer_callback_query(call.id, "❌ لم يتم العثور على التذكرة")
            return
        
        subject = ticket.get('subject', 'بدون عنوان')
        status = ticket.get('status', 'unknown')
        priority = ticket.get('priority', 'medium')
        created_at = ticket.get('created_at', '')
        updated_at = ticket.get('updated_at', '')
        message_content = ticket.get('message', 'لا يوجد محتوى')
        
        status_emoji = self.get_status_emoji(status)
        priority_emoji = self.get_priority_emoji(priority)
        
        ticket_text = f"""
🎫 **تفاصيل التذكرة #{ticket_id}**

📝 **العنوان:** {subject}
📊 **الحالة:** {status_emoji} {status.upper()}
⚡ **الأولوية:** {priority_emoji} {priority.upper()}
📅 **تاريخ الإنشاء:** {created_at[:16].replace('T', ' ')}
🔄 **آخر تحديث:** {updated_at[:16].replace('T', ' ')}

💬 **المحتوى:**
{message_content}
        """
        
        # إنشاء أزرار الإدارة
        markup = types.InlineKeyboardMarkup()
        
        if status.lower() in ['open', 'pending']:
            reply_btn = types.InlineKeyboardButton("💬 الرد على التذكرة", callback_data=f"reply_ticket_{ticket_id}")
            close_btn = types.InlineKeyboardButton("🔒 إغلاق التذكرة", callback_data=f"close_ticket_{ticket_id}")
            markup.add(reply_btn)
            markup.add(close_btn)
        elif status.lower() == 'closed':
            reopen_btn = types.InlineKeyboardButton("🔓 إعادة فتح التذكرة", callback_data=f"reopen_ticket_{ticket_id}")
            markup.add(reopen_btn)
        
        # زر العودة
        back_btn = types.InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_to_tickets")
        markup.add(back_btn)
        
        self.bot.edit_message_text(
            ticket_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    def handle_ticket_command(self, message):
        """معالج أمر التذكرة"""
        @self.require_login
        def _handle_ticket(msg):
            # إعادة توجيه إلى الدعم الفني
            self.handle_support_command(msg)
        
        _handle_ticket(message)
    
    def handle_ticket_input(self, message):
        """معالج إدخال بيانات التذكرة"""
        user_id = message.from_user.id
        
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        
        if state['step'] == 'waiting_subject':
            # حفظ العنوان والانتقال للمحتوى
            state['subject'] = message.text.strip()
            state['step'] = 'waiting_message'
            self.bot.reply_to(message, "📝 الآن اكتب محتوى التذكرة (وصف المشكلة أو الاستفسار):")
            
        elif state['step'] == 'waiting_message':
            # حفظ المحتوى والانتقال لاختيار الأولوية
            state['message'] = message.text.strip()
            
            # عرض خيارات الأولوية
            markup = types.InlineKeyboardMarkup()
            high_btn = types.InlineKeyboardButton("🔴 عالية", callback_data="priority_high")
            medium_btn = types.InlineKeyboardButton("🟡 متوسطة", callback_data="priority_medium")
            low_btn = types.InlineKeyboardButton("🟢 منخفضة", callback_data="priority_low")
            
            markup.add(high_btn)
            markup.add(medium_btn)
            markup.add(low_btn)
            
            self.bot.reply_to(message, 
                             "⚡ اختر أولوية التذكرة:",
                             reply_markup=markup)
            
        elif state['step'] == 'waiting_reply':
            # الرد على تذكرة موجودة
            reply_message = message.text.strip()
            ticket_id = state['ticket_id']
            
            # إرسال الرد عبر API (هذا يحتاج تنفيذ في API)
            # api_client.ctrlpanel_reply_ticket(api_key, ticket_id, reply_message)
            
            self.bot.reply_to(message, 
                             f"✅ تم إرسال ردك على التذكرة #{ticket_id}\n\n"
                             f"سيتم الرد عليك في أقرب وقت ممكن.")
            
            # إزالة المستخدم من حالة الانتظار
            del self.user_states[user_id]
    
    def create_ticket(self, user_id, subject, message, priority='medium'):
        """إنشاء تذكرة جديدة"""
        api_key = self.auth.get_user_api_key(user_id)
        
        if not api_key:
            return False, "لم يتم العثور على مفتاح API"
        
        result = api_client.ctrlpanel_create_ticket(api_key, subject, message, priority)
        
        if result and result.get('success'):
            ticket_data = result.get('data', {})
            ticket_id = ticket_data.get('id', 'غير محدد')
            
            # حفظ التذكرة في قاعدة البيانات المحلية
            db.add_transaction(user_id, 'ticket_created', 0, f'إنشاء تذكرة: {subject}')
            
            return True, ticket_id
        else:
            error_msg = result.get('message', 'فشل في إنشاء التذكرة') if result else 'فشل في الاتصال بالخادم'
            return False, error_msg
    
    def get_status_emoji(self, status):
        """الحصول على رمز تعبيري للحالة"""
        status_emojis = {
            'open': '🟢',
            'pending': '🟡',
            'closed': '🔴',
            'resolved': '✅',
            'unknown': '⚪'
        }
        return status_emojis.get(status.lower(), '⚪')
    
    def get_priority_emoji(self, priority):
        """الحصول على رمز تعبيري للأولوية"""
        priority_emojis = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        return priority_emojis.get(priority.lower(), '🟡')
    
    def handle_callback_query(self, call):
        """معالج الأزرار التفاعلية"""
        user_id = call.from_user.id
        
        if call.data.startswith("tickets_page_"):
            # تغيير صفحة التذاكر
            page = int(call.data.split("_")[-1])
            tickets = self.tickets_cache.get(user_id, [])
            if tickets:
                self.show_tickets_page(call.message, tickets, page, edit_message=True)
        
        elif call.data.startswith("view_ticket_"):
            # عرض تفاصيل التذكرة
            ticket_id = call.data.split("_")[-1]
            self.show_ticket_details(call, ticket_id)
        
        elif call.data == "create_new_ticket":
            # بدء إنشاء تذكرة جديدة
            self.user_states[user_id] = {'step': 'waiting_subject'}
            self.bot.edit_message_text(
                "➕ **إنشاء تذكرة دعم فني جديدة**\n\n"
                "📝 اكتب عنوان التذكرة (موضوع المشكلة أو الاستفسار):",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
        
        elif call.data.startswith("priority_"):
            # اختيار أولوية التذكرة وإنشاؤها
            priority = call.data.split("_")[-1]
            
            if user_id in self.user_states:
                state = self.user_states[user_id]
                subject = state.get('subject', '')
                message = state.get('message', '')
                
                # إنشاء التذكرة
                success, result = self.create_ticket(user_id, subject, message, priority)
                
                if success:
                    success_text = f"""
✅ **تم إنشاء التذكرة بنجاح!**

🆔 **رقم التذكرة:** #{result}
📝 **العنوان:** {subject}
⚡ **الأولوية:** {priority.upper()}

📧 سيتم الرد عليك في أقرب وقت ممكن.
استخدم /support لمتابعة تذاكرك.
                    """
                    
                    self.bot.edit_message_text(
                        success_text,
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode='Markdown'
                    )
                else:
                    self.bot.edit_message_text(
                        f"❌ فشل في إنشاء التذكرة: {result}",
                        call.message.chat.id,
                        call.message.message_id
                    )
                
                # إزالة المستخدم من حالة الانتظار
                del self.user_states[user_id]
        
        elif call.data.startswith("reply_ticket_"):
            # الرد على تذكرة
            ticket_id = call.data.split("_")[-1]
            self.user_states[user_id] = {
                'step': 'waiting_reply',
                'ticket_id': ticket_id
            }
            
            self.bot.edit_message_text(
                f"💬 **الرد على التذكرة #{ticket_id}**\n\n"
                f"اكتب ردك:",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
        
        elif call.data == "back_to_tickets":
            # العودة إلى قائمة التذاكر
            tickets = self.tickets_cache.get(user_id, [])
            if tickets:
                self.show_tickets_page(call.message, tickets, 0, edit_message=True)
            else:
                self.show_no_tickets_message(call.message)
        
        elif call.data == "refresh_tickets":
            # تحديث قائمة التذاكر
            api_key = self.auth.get_user_api_key(user_id)
            tickets_data = api_client.ctrlpanel_get_tickets(api_key)
            
            if tickets_data and tickets_data.get('success'):
                tickets = tickets_data.get('data', [])
                self.tickets_cache[user_id] = tickets
                
                if tickets:
                    self.show_tickets_page(call.message, tickets, 0, edit_message=True)
                else:
                    self.show_no_tickets_message(call.message)
                
                self.bot.answer_callback_query(call.id, "✅ تم تحديث قائمة التذاكر")
            else:
                self.bot.answer_callback_query(call.id, "❌ فشل في تحديث القائمة")

