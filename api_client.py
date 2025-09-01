# -*- coding: utf-8 -*-
"""
عميل API للتكامل مع CtrlPanel و Pterodactyl
"""

import requests
import json
from typing import Dict, Any, Optional, List
from config import config

class APIClient:
    def __init__(self):
        self.ctrlpanel_base_url = config.CTRLPANEL_API_URL
        self.pterodactyl_base_url = config.PTERODACTYL_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, url: str, headers: Dict = None, 
                     data: Dict = None, params: Dict = None) -> Optional[Dict]:
        """إجراء طلب HTTP"""
        try:
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)
            
            response = self.session.request(
                method=method,
                url=url,
                headers=request_headers,
                json=data,
                params=params,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"خطأ في الطلب: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"خطأ في الاتصال: {e}")
            return None
    
    # CtrlPanel API Methods
    def ctrlpanel_login(self, email: str, password: str) -> Optional[Dict]:
        """تسجيل الدخول إلى CtrlPanel"""
        url = f"{self.ctrlpanel_base_url}/auth/login"
        data = {
            "email": email,
            "password": password
        }
        return self._make_request('POST', url, data=data)
    
    def ctrlpanel_get_user_info(self, api_key: str) -> Optional[Dict]:
        """الحصول على معلومات المستخدم من CtrlPanel"""
        url = f"{self.ctrlpanel_base_url}/user"
        headers = {'Authorization': f'Bearer {api_key}'}
        return self._make_request('GET', url, headers=headers)
    
    def ctrlpanel_get_balance(self, api_key: str) -> Optional[Dict]:
        """الحصول على رصيد المستخدم"""
        url = f"{self.ctrlpanel_base_url}/user/balance"
        headers = {'Authorization': f'Bearer {api_key}'}
        return self._make_request('GET', url, headers=headers)
    
    def ctrlpanel_redeem_coupon(self, api_key: str, coupon_code: str) -> Optional[Dict]:
        """تفعيل كوبون شحن"""
        url = f"{self.ctrlpanel_base_url}/user/redeem-coupon"
        headers = {'Authorization': f'Bearer {api_key}'}
        data = {'coupon_code': coupon_code}
        return self._make_request('POST', url, headers=headers, data=data)
    
    def ctrlpanel_get_products(self) -> Optional[Dict]:
        """الحصول على قائمة المنتجات"""
        url = f"{self.ctrlpanel_base_url}/products"
        return self._make_request('GET', url)
    
    def ctrlpanel_purchase_product(self, api_key: str, product_id: str, 
                                  quantity: int = 1) -> Optional[Dict]:
        """شراء منتج"""
        url = f"{self.ctrlpanel_base_url}/user/purchase"
        headers = {'Authorization': f'Bearer {api_key}'}
        data = {
            'product_id': product_id,
            'quantity': quantity
        }
        return self._make_request('POST', url, headers=headers, data=data)
    
    def ctrlpanel_get_tickets(self, api_key: str) -> Optional[Dict]:
        """الحصول على تذاكر المستخدم"""
        url = f"{self.ctrlpanel_base_url}/user/tickets"
        headers = {'Authorization': f'Bearer {api_key}'}
        return self._make_request('GET', url, headers=headers)
    
    def ctrlpanel_create_ticket(self, api_key: str, subject: str, 
                               message: str, priority: str = 'medium') -> Optional[Dict]:
        """إنشاء تذكرة دعم فني جديدة"""
        url = f"{self.ctrlpanel_base_url}/user/tickets"
        headers = {'Authorization': f'Bearer {api_key}'}
        data = {
            'subject': subject,
            'message': message,
            'priority': priority
        }
        return self._make_request('POST', url, headers=headers, data=data)
    
    def ctrlpanel_get_referral_info(self, api_key: str) -> Optional[Dict]:
        """الحصول على معلومات نظام الإحالة"""
        url = f"{self.ctrlpanel_base_url}/user/referral"
        headers = {'Authorization': f'Bearer {api_key}'}
        return self._make_request('GET', url, headers=headers)
    
    # Pterodactyl API Methods
    def pterodactyl_get_servers(self, api_key: str) -> Optional[Dict]:
        """الحصول على قائمة السيرفرات من Pterodactyl"""
        url = f"{self.pterodactyl_base_url}/client"
        headers = {'Authorization': f'Bearer {api_key}'}
        return self._make_request('GET', url, headers=headers)
    
    def pterodactyl_get_server_details(self, api_key: str, server_id: str) -> Optional[Dict]:
        """الحصول على تفاصيل سيرفر محدد"""
        url = f"{self.pterodactyl_base_url}/client/servers/{server_id}"
        headers = {'Authorization': f'Bearer {api_key}'}
        return self._make_request('GET', url, headers=headers)
    
    def pterodactyl_get_server_resources(self, api_key: str, server_id: str) -> Optional[Dict]:
        """الحصول على استهلاك موارد السيرفر"""
        url = f"{self.pterodactyl_base_url}/client/servers/{server_id}/resources"
        headers = {'Authorization': f'Bearer {api_key}'}
        return self._make_request('GET', url, headers=headers)
    
    def pterodactyl_send_power_action(self, api_key: str, server_id: str, 
                                     action: str) -> Optional[Dict]:
        """إرسال أمر تشغيل/إيقاف للسيرفر"""
        url = f"{self.pterodactyl_base_url}/client/servers/{server_id}/power"
        headers = {'Authorization': f'Bearer {api_key}'}
        data = {'signal': action}  # start, stop, restart, kill
        return self._make_request('POST', url, headers=headers, data=data)
    
    def pterodactyl_send_command(self, api_key: str, server_id: str, 
                                command: str) -> Optional[Dict]:
        """إرسال أمر إلى السيرفر"""
        url = f"{self.pterodactyl_base_url}/client/servers/{server_id}/command"
        headers = {'Authorization': f'Bearer {api_key}'}
        data = {'command': command}
        return self._make_request('POST', url, headers=headers, data=data)
    
    def pterodactyl_get_server_logs(self, api_key: str, server_id: str) -> Optional[Dict]:
        """الحصول على سجلات السيرفر"""
        url = f"{self.pterodactyl_base_url}/client/servers/{server_id}/logs"
        headers = {'Authorization': f'Bearer {api_key}'}
        return self._make_request('GET', url, headers=headers)

# إنشاء كائن عميل API
api_client = APIClient()

