# -*- coding: utf-8 -*-
"""
وحدة إدارة المتجر والمنتجات
"""

import telebot
from telebot import types
from database import db
from api_client import api_client
import math

class StoreManager:
    def __init__(self, bot: telebot.TeleBot, auth_manager):
        self.bot = bot
        self.auth = auth_manager
        self.user_states = {}
        self.products_cache = {}  # تخزين مؤقت للمنتجات
    
    def register_handlers(self):
        """تسجيل معالجات الأوامر"""
        self.bot.message_handler(commands=['store'])(self.handle_store_command)
        self.bot.message_handler(commands=['buy'])(self.handle_buy_command)
        self.bot.message_handler(func=lambda message: self.is_waiting_for_purchase_input(message))(self.handle_purchase_input)
    
    def is_waiting_for_purchase_input(self, message):
        """التحقق من أن المستخدم في حالة انتظار إدخال بيانات الشراء"""
        return (message.from_user.id in self.user_states and 
                'step' in self.user_states[message.from_user.id])
    
    @property
    def require_login(self):
        """ديكوريتر للتحقق من تسجيل الدخول"""
        return self.auth.require_login
    
    def handle_store_command(self, message):
        """معالج أمر عرض المتجر"""
        @self.require_login
        def _handle_store(msg):
            user_id = msg.from_user.id
            
            # الحصول على المنتجات من API
            products_data = api_client.ctrlpanel_get_products()
            
            if not products_data or not products_data.get('success'):
                self.bot.reply_to(msg, "❌ فشل في تحميل المنتجات. حاول مرة أخرى لاحقاً.")
                return
            
            products = products_data.get('data', [])
            if not products:
                self.bot.reply_to(msg, "📦 المتجر فارغ حالياً. تحقق لاحقاً!")
                return
            
            # حفظ المنتجات في التخزين المؤقت
            self.products_cache[user_id] = products
            
            # إنشاء قائمة المنتجات مع الأزرار
            self.show_products_page(msg, products, 0)
        
        _handle_store(message)
    
    def show_products_page(self, message, products, page=0, edit_message=False):
        """عرض صفحة من المنتجات"""
        products_per_page = 5
        total_pages = math.ceil(len(products) / products_per_page)
        start_idx = page * products_per_page
        end_idx = start_idx + products_per_page
        page_products = products[start_idx:end_idx]
        
        store_text = f"🛒 **متجر منصة Nexo** (صفحة {page + 1}/{total_pages})\n\n"
        
        # إنشاء الأزرار للمنتجات
        markup = types.InlineKeyboardMarkup()
        
        for i, product in enumerate(page_products):
            product_name = product.get('name', 'منتج غير محدد')
            product_price = product.get('price', 0)
            product_id = product.get('id')
            
            # إضافة معلومات المنتج إلى النص
            store_text += f"🔹 **{product_name}**\n"
            store_text += f"💰 السعر: `{product_price:.2f}` كوين\n"
            store_text += f"📝 الوصف: {product.get('description', 'لا يوجد وصف')}\n\n"
            
            # زر الشراء
            buy_btn = types.InlineKeyboardButton(
                f"🛒 شراء {product_name}",
                callback_data=f"buy_product_{product_id}"
            )
            markup.add(buy_btn)
        
        # أزرار التنقل بين الصفحات
        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton("⬅️ السابق", callback_data=f"store_page_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton("➡️ التالي", callback_data=f"store_page_{page+1}"))
        
        if nav_buttons:
            markup.add(*nav_buttons)
        
        # زر تحديث المتجر
        refresh_btn = types.InlineKeyboardButton("🔄 تحديث المتجر", callback_data="refresh_store")
        markup.add(refresh_btn)
        
        if edit_message:
            self.bot.edit_message_text(
                store_text,
                message.chat.id,
                message.message_id,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        else:
            self.bot.reply_to(message, store_text, reply_markup=markup, parse_mode='Markdown')
    
    def handle_buy_command(self, message):
        """معالج أمر الشراء المباشر"""
        @self.require_login
        def _handle_buy(msg):
            # إعادة توجيه إلى المتجر
            self.handle_store_command(msg)
        
        _handle_buy(message)
    
    def handle_purchase_input(self, message):
        """معالج إدخال بيانات الشراء"""
        user_id = message.from_user.id
        
        if user_id not in self.user_states:
            return
        
        state = self.user_states[user_id]
        
        if state['step'] == 'waiting_quantity':
            try:
                quantity = int(message.text.strip())
                if quantity <= 0:
                    self.bot.reply_to(message, "❌ الكمية يجب أن تكون أكبر من صفر!")
                    return
                
                # تنفيذ عملية الشراء
                self.execute_purchase(message, state['product_id'], quantity)
                
            except ValueError:
                self.bot.reply_to(message, "❌ يرجى إدخال رقم صحيح للكمية!")
        
        elif state['step'] == 'waiting_server_name':
            server_name = message.text.strip()
            if len(server_name) < 3:
                self.bot.reply_to(message, "❌ اسم السيرفر يجب أن يكون 3 أحرف على الأقل!")
                return
            
            # حفظ اسم السيرفر ومتابعة الشراء
            state['server_name'] = server_name
            self.execute_purchase(message, state['product_id'], state.get('quantity', 1))
    
    def execute_purchase(self, message, product_id, quantity=1):
        """تنفيذ عملية الشراء"""
        user_id = message.from_user.id
        
        # إزالة المستخدم من حالة الانتظار
        if user_id in self.user_states:
            del self.user_states[user_id]
        
        api_key = self.auth.get_user_api_key(user_id)
        if not api_key:
            self.bot.reply_to(message, "❌ لم يتم العثور على مفتاح API.")
            return
        
        # الحصول على تفاصيل المنتج
        products = self.products_cache.get(user_id, [])
        product = next((p for p in products if str(p.get('id')) == str(product_id)), None)
        
        if not product:
            self.bot.reply_to(message, "❌ لم يتم العثور على المنتج. حاول تحديث المتجر.")
            return
        
        product_name = product.get('name', 'منتج غير محدد')
        product_price = product.get('price', 0)
        total_price = product_price * quantity
        
        # التحقق من الرصيد
        balance_info = api_client.ctrlpanel_get_balance(api_key)
        if balance_info and balance_info.get('success'):
            current_balance = balance_info.get('data', {}).get('balance', 0)
            if current_balance < total_price:
                self.bot.reply_to(message, 
                                 f"❌ **رصيد غير كافي!**\n\n"
                                 f"💰 رصيدك الحالي: `{current_balance:.2f}` كوين\n"
                                 f"💳 المطلوب: `{total_price:.2f}` كوين\n"
                                 f"📉 النقص: `{total_price - current_balance:.2f}` كوين\n\n"
                                 f"استخدم /coupon لشحن رصيدك.",
                                 parse_mode='Markdown')
                return
        
        # محاولة الشراء
        purchase_result = api_client.ctrlpanel_purchase_product(api_key, product_id, quantity)
        
        if purchase_result and purchase_result.get('success'):
            # نجح الشراء
            purchase_data = purchase_result.get('data', {})
            server_id = purchase_data.get('server_id')
            
            # حفظ السيرفر في قاعدة البيانات إذا كان منتج سيرفر
            if server_id:
                server_name = self.user_states.get(user_id, {}).get('server_name', product_name)
                db.add_server(user_id, server_id, server_name, product_name)
            
            # حفظ المعاملة
            db.add_transaction(user_id, 'purchase', -total_price, f'شراء {product_name} (الكمية: {quantity})')
            
            success_text = f"""
✅ **تم الشراء بنجاح!**

🛒 **المنتج:** {product_name}
📦 **الكمية:** {quantity}
💰 **المبلغ المدفوع:** `{total_price:.2f}` كوين
💳 **الرصيد المتبقي:** `{current_balance - total_price:.2f}` كوين
            """
            
            if server_id:
                success_text += f"\n🖥️ **معرف السيرفر:** `{server_id}`"
                success_text += f"\n\nاستخدم /servers لإدارة سيرفراتك."
            
            success_text += f"\n\nشكراً لاستخدامك منصة Nexo! 🎉"
            
            self.bot.reply_to(message, success_text, parse_mode='Markdown')
            
        else:
            error_msg = purchase_result.get('message', 'فشل في عملية الشراء') if purchase_result else 'فشل في الاتصال بالخادم'
            self.bot.reply_to(message, f"❌ فشل في الشراء: {error_msg}")
    
    def handle_callback_query(self, call):
        """معالج الأزرار التفاعلية"""
        user_id = call.from_user.id
        
        if call.data.startswith("store_page_"):
            # تغيير صفحة المتجر
            page = int(call.data.split("_")[-1])
            products = self.products_cache.get(user_id, [])
            if products:
                self.show_products_page(call.message, products, page, edit_message=True)
        
        elif call.data.startswith("buy_product_"):
            # بدء عملية الشراء
            product_id = call.data.split("_")[-1]
            products = self.products_cache.get(user_id, [])
            product = next((p for p in products if str(p.get('id')) == str(product_id)), None)
            
            if not product:
                self.bot.answer_callback_query(call.id, "❌ لم يتم العثور على المنتج")
                return
            
            product_name = product.get('name', 'منتج غير محدد')
            product_price = product.get('price', 0)
            
            # التحقق من نوع المنتج
            if 'server' in product_name.lower():
                # منتج سيرفر - طلب اسم السيرفر
                self.user_states[user_id] = {
                    'step': 'waiting_server_name',
                    'product_id': product_id,
                    'quantity': 1
                }
                
                self.bot.edit_message_text(
                    f"🖥️ **شراء {product_name}**\n\n"
                    f"💰 السعر: `{product_price:.2f}` كوين\n\n"
                    f"📝 أدخل اسم السيرفر:",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
            else:
                # منتج عادي - طلب الكمية
                self.user_states[user_id] = {
                    'step': 'waiting_quantity',
                    'product_id': product_id
                }
                
                self.bot.edit_message_text(
                    f"🛒 **شراء {product_name}**\n\n"
                    f"💰 السعر: `{product_price:.2f}` كوين\n\n"
                    f"📦 أدخل الكمية المطلوبة:",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='Markdown'
                )
        
        elif call.data == "refresh_store":
            # تحديث المتجر
            products_data = api_client.ctrlpanel_get_products()
            
            if products_data and products_data.get('success'):
                products = products_data.get('data', [])
                self.products_cache[user_id] = products
                self.show_products_page(call.message, products, 0, edit_message=True)
                self.bot.answer_callback_query(call.id, "✅ تم تحديث المتجر")
            else:
                self.bot.answer_callback_query(call.id, "❌ فشل في تحديث المتجر")

