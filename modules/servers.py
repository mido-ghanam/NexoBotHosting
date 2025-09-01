# -*- coding: utf-8 -*-
"""
وحدة إدارة السيرفرات
"""

import telebot
from telebot import types
from database import db
from api_client import api_client
import math

class ServerManager:
    def __init__(self, bot: telebot.TeleBot, auth_manager):
        self.bot = bot
        self.auth = auth_manager
        self.user_states = {}
        self.servers_cache = {}
    
    def register_handlers(self):
        """تسجيل معالجات الأوامر"""
        self.bot.message_handler(commands=['servers'])(self.handle_servers_command)
        self.bot.message_handler(commands=['server'])(self.handle_server_command)
        self.bot.message_handler(func=lambda message: self.is_waiting_for_server_input(message))(self.handle_server_input)
    
    def is_waiting_for_server_input(self, message):
        """التحقق من أن المستخدم في حالة انتظار إدخال بيانات السيرفر"""
        return (message.from_user.id in self.user_states and 
                'step' in self.user_states[message.from_user.id])
    
    @property
    def require_login(self):
        """ديكوريتر للتحقق من تسجيل الدخول"""
        return self.auth.require_login
    
    def handle_servers_command(self, message):
        """معالج أمر عرض السيرفرات"""
        @self.require_login
        def _handle_servers(msg):
            user_id = msg.from_user.id
            api_key = self.auth.get_user_api_key(user_id)
            
            if not api_key:
                self.bot.reply_to(msg, "❌ لم يتم العثور على مفتاح API.")
                return
            
            # الحصول على السيرفرات من Pterodactyl
            servers_data = api_client.pterodactyl_get_servers(api_key)
            
            if not servers_data or not servers_data.get('object') == 'list':
                self.bot.reply_to(msg, "❌ فشل في تحميل السيرفرات. تحقق من الاتصال.")
                return
            
            servers = servers_data.get('data', [])
            if not servers:
                self.bot.reply_to(msg, 
                                 "🖥️ **لا توجد سيرفرات**\n\n"
                                 "لم يتم العثور على أي سيرفرات مرتبطة بحسابك.\n"
                                 "استخدم /store لشراء سيرفر جديد!")
                return
            
            # حفظ السيرفرات في التخزين المؤقت
            self.servers_cache[user_id] = servers
            
            # عرض قائمة السيرفرات
            self.show_servers_page(msg, servers, 0)
        
        _handle_servers(message)
    
    def show_servers_page(self, message, servers, page=0, edit_message=False):
        """عرض صفحة من السيرفرات"""
        servers_per_page = 3
        total_pages = math.ceil(len(servers) / servers_per_page)
        start_idx = page * servers_per_page
        end_idx = start_idx + servers_per_page
        page_servers = servers[start_idx:end_idx]
        
        servers_text = f"🖥️ **سيرفراتك** (صفحة {page + 1}/{total_pages})\n\n"
        
        # إنشاء الأزرار للسيرفرات
        markup = types.InlineKeyboardMarkup()
        
        for server in page_servers:
            server_attrs = server.get('attributes', {})
            server_name = server_attrs.get('name', 'سيرفر غير محدد')
            server_id = server_attrs.get('identifier', 'غير محدد')
            server_status = self.get_status_emoji(server_attrs.get('status', 'unknown'))
            
            # معلومات السيرفر
            limits = server_attrs.get('limits', {})
            memory = limits.get('memory', 0)
            cpu = limits.get('cpu', 0)
            disk = limits.get('disk', 0)
            
            servers_text += f"🔹 **{server_name}** {server_status}\n"
            servers_text += f"🆔 المعرف: `{server_id}`\n"
            servers_text += f"💾 الذاكرة: `{memory}` MB\n"
            servers_text += f"⚡ المعالج: `{cpu}%`\n"
            servers_text += f"💽 التخزين: `{disk}` MB\n\n"
            
            # زر إدارة السيرفر
            manage_btn = types.InlineKeyboardButton(
                f"⚙️ إدارة {server_name}",
                callback_data=f"manage_server_{server_id}"
            )
            markup.add(manage_btn)
        
        # أزرار التنقل
        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton("⬅️ السابق", callback_data=f"servers_page_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton("➡️ التالي", callback_data=f"servers_page_{page+1}"))
        
        if nav_buttons:
            markup.add(*nav_buttons)
        
        # زر تحديث القائمة
        refresh_btn = types.InlineKeyboardButton("🔄 تحديث القائمة", callback_data="refresh_servers")
        markup.add(refresh_btn)
        
        if edit_message:
            self.bot.edit_message_text(
                servers_text,
                message.chat.id,
                message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        else:
            self.bot.reply_to(message, servers_text, reply_markup=markup, parse_mode='Markdown')
    
    def show_server_management(self, call, server_id):
        """عرض لوحة إدارة السيرفر"""
        user_id = call.from_user.id
        api_key = self.auth.get_user_api_key(user_id)
        
        # الحصول على تفاصيل السيرفر
        server_details = api_client.pterodactyl_get_server_details(api_key, server_id)
        server_resources = api_client.pterodactyl_get_server_resources(api_key, server_id)
        
        if not server_details or not server_details.get('attributes'):
            self.bot.answer_callback_query(call.id, "❌ فشل في تحميل تفاصيل السيرفر")
            return
        
        server_attrs = server_details.get('attributes', {})
        server_name = server_attrs.get('name', 'سيرفر غير محدد')
        server_status = server_attrs.get('status', 'unknown')
        status_emoji = self.get_status_emoji(server_status)
        
        # معلومات الموارد
        limits = server_attrs.get('limits', {})
        memory_limit = limits.get('memory', 0)
        cpu_limit = limits.get('cpu', 0)
        disk_limit = limits.get('disk', 0)
        
        # الاستهلاك الحالي
        current_usage = {}
        if server_resources and server_resources.get('attributes'):
            resources = server_resources.get('attributes', {})
            current_usage = {
                'memory': resources.get('memory_bytes', 0) / (1024 * 1024),  # تحويل إلى MB
                'cpu': resources.get('cpu_absolute', 0),
                'disk': resources.get('disk_bytes', 0) / (1024 * 1024)  # تحويل إلى MB
            }
        
        management_text = f"""
🖥️ **إدارة السيرفر: {server_name}**

📊 **الحالة:** {status_emoji} {server_status.upper()}
🆔 **المعرف:** `{server_id}`

📈 **استهلاك الموارد:**
💾 الذاكرة: `{current_usage.get('memory', 0):.0f}/{memory_limit}` MB
⚡ المعالج: `{current_usage.get('cpu', 0):.1f}%` (الحد الأقصى: {cpu_limit}%)
💽 التخزين: `{current_usage.get('disk', 0):.0f}/{disk_limit}` MB
        """
        
        # إنشاء أزرار الإدارة
        markup = types.InlineKeyboardMarkup()
        
        # أزرار التحكم في الطاقة
        if server_status == 'offline':
            power_btn = types.InlineKeyboardButton("▶️ تشغيل", callback_data=f"power_start_{server_id}")
        elif server_status == 'online':
            power_btn = types.InlineKeyboardButton("⏹️ إيقاف", callback_data=f"power_stop_{server_id}")
        else:
            power_btn = types.InlineKeyboardButton("🔄 إعادة تشغيل", callback_data=f"power_restart_{server_id}")
        
        markup.add(power_btn)
        
        # أزرار إضافية
        restart_btn = types.InlineKeyboardButton("🔄 إعادة تشغيل", callback_data=f"power_restart_{server_id}")
        kill_btn = types.InlineKeyboardButton("⚠️ إيقاف قسري", callback_data=f"power_kill_{server_id}")
        markup.add(restart_btn, kill_btn)
        
        # أزرار المعلومات
        logs_btn = types.InlineKeyboardButton("📜 السجلات", callback_data=f"show_logs_{server_id}")
        console_btn = types.InlineKeyboardButton("💻 وحدة التحكم", callback_data=f"show_console_{server_id}")
        markup.add(logs_btn, console_btn)
        
        # زر العودة
        back_btn = types.InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_to_servers")
        markup.add(back_btn)
        
        self.bot.edit_message_text(
            management_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    def handle_server_command(self, message):
        """معالج أمر السيرفر المحدد"""
        @self.require_login
        def _handle_server(msg):
            # إعادة توجيه إلى قائمة السيرفرات
            self.handle_servers_command(msg)
        
        _handle_server(message)
    
    def handle_server_input(self, message):
        """معالج إدخال أوامر السيرفر"""
        user_id = message.from_user.id
        
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        
        if state['step'] == 'waiting_command':
            command = message.text.strip()
            server_id = state['server_id']
            
            # إرسال الأمر إلى السيرفر
            api_key = self.auth.get_user_api_key(user_id)
            result = api_client.pterodactyl_send_command(api_key, server_id, command)
            
            if result:
                self.bot.reply_to(message, f"✅ تم إرسال الأمر: `{command}`", parse_mode='Markdown')
            else:
                self.bot.reply_to(message, f"❌ فشل في إرسال الأمر: `{command}`", parse_mode='Markdown')
            
            # إزالة المستخدم من حالة الانتظار
            del self.user_states[user_id]
    
    def get_status_emoji(self, status):
        """الحصول على رمز تعبيري للحالة"""
        status_emojis = {
            'online': '🟢',
            'offline': '🔴',
            'starting': '🟡',
            'stopping': '🟠',
            'unknown': '⚪'
        }
        return status_emojis.get(status.lower(), '⚪')
    
    def handle_callback_query(self, call):
        """معالج الأزرار التفاعلية"""
        user_id = call.from_user.id
        api_key = self.auth.get_user_api_key(user_id)
        
        if call.data.startswith("servers_page_"):
            # تغيير صفحة السيرفرات
            page = int(call.data.split("_")[-1])
            servers = self.servers_cache.get(user_id, [])
            if servers:
                self.show_servers_page(call.message, servers, page, edit_message=True)
        
        elif call.data.startswith("manage_server_"):
            # إدارة سيرفر محدد
            server_id = call.data.split("_")[-1]
            self.show_server_management(call, server_id)
        
        elif call.data.startswith("power_"):
            # أوامر الطاقة
            parts = call.data.split("_")
            action = parts[1]
            server_id = parts[2]
            
            result = api_client.pterodactyl_send_power_action(api_key, server_id, action)
            
            if result:
                action_names = {
                    'start': 'تشغيل',
                    'stop': 'إيقاف',
                    'restart': 'إعادة تشغيل',
                    'kill': 'إيقاف قسري'
                }
                action_name = action_names.get(action, action)
                self.bot.answer_callback_query(call.id, f"✅ تم {action_name} السيرفر")
                
                # تحديث عرض السيرفر
                self.show_server_management(call, server_id)
            else:
                self.bot.answer_callback_query(call.id, "❌ فشل في تنفيذ الأمر")
        
        elif call.data.startswith("show_logs_"):
            # عرض سجلات السيرفر
            server_id = call.data.split("_")[-1]
            logs_data = api_client.pterodactyl_get_server_logs(api_key, server_id)
            
            if logs_data and logs_data.get('data'):
                logs = logs_data.get('data', [])
                logs_text = "📜 **سجلات السيرفر:**\n\n"
                
                # عرض آخر 10 سجلات
                for log in logs[-10:]:
                    logs_text += f"`{log}`\n"
                
                if len(logs_text) > 4000:
                    logs_text = logs_text[:3900] + "\n\n... المزيد من السجلات"
                
                self.bot.edit_message_text(
                    logs_text,
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
            else:
                self.bot.answer_callback_query(call.id, "❌ فشل في تحميل السجلات")
        
        elif call.data.startswith("show_console_"):
            # عرض وحدة التحكم
            server_id = call.data.split("_")[-1]
            self.user_states[user_id] = {
                'step': 'waiting_command',
                'server_id': server_id
            }
            
            self.bot.edit_message_text(
                f"💻 **وحدة التحكم**\n\n"
                f"🖥️ السيرفر: `{server_id}`\n\n"
                f"أدخل الأمر الذي تريد تنفيذه:",
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown'
            )
        
        elif call.data == "back_to_servers":
            # العودة إلى قائمة السيرفرات
            servers = self.servers_cache.get(user_id, [])
            if servers:
                self.show_servers_page(call.message, servers, 0, edit_message=True)
            else:
                self.bot.answer_callback_query(call.id, "❌ لا توجد سيرفرات محفوظة")
        
        elif call.data == "refresh_servers":
            # تحديث قائمة السيرفرات
            servers_data = api_client.pterodactyl_get_servers(api_key)
            
            if servers_data and servers_data.get('object') == 'list':
                servers = servers_data.get('data', [])
                self.servers_cache[user_id] = servers
                self.show_servers_page(call.message, servers, 0, edit_message=True)
                self.bot.answer_callback_query(call.id, "✅ تم تحديث قائمة السيرفرات")
            else:
                self.bot.answer_callback_query(call.id, "❌ فشل في تحديث القائمة")

