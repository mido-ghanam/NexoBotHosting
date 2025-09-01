# -*- coding: utf-8 -*-
"""
إدارة قاعدة البيانات لبوت تيليجرام
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import config

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # جدول المستخدمين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    email TEXT,
                    api_key TEXT,
                    is_logged_in BOOLEAN DEFAULT FALSE,
                    balance REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    language TEXT DEFAULT 'ar'
                )
            ''')
            
            # جدول السيرفرات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    server_id TEXT,
                    server_name TEXT,
                    server_type TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                )
            ''')
            
            # جدول التذاكر
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    ticket_id TEXT,
                    subject TEXT,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                )
            ''')
            
            # جدول المعاملات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    transaction_type TEXT,
                    amount REAL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                )
            ''')
            
            conn.commit()
    
    def add_user(self, telegram_id: int, email: str = None, api_key: str = None) -> bool:
        """إضافة مستخدم جديد"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (telegram_id, email, api_key, is_logged_in, last_login)
                    VALUES (?, ?, ?, ?, ?)
                ''', (telegram_id, email, api_key, True, datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            print(f"خطأ في إضافة المستخدم: {e}")
            return False
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على بيانات المستخدم"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"خطأ في الحصول على المستخدم: {e}")
            return None
    
    def update_user_login_status(self, telegram_id: int, is_logged_in: bool) -> bool:
        """تحديث حالة تسجيل الدخول للمستخدم"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET is_logged_in = ?, last_login = ?
                    WHERE telegram_id = ?
                ''', (is_logged_in, datetime.now() if is_logged_in else None, telegram_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"خطأ في تحديث حالة تسجيل الدخول: {e}")
            return False
    
    def add_server(self, telegram_id: int, server_id: str, server_name: str, 
                   server_type: str, status: str = 'active') -> bool:
        """إضافة سيرفر جديد"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO servers 
                    (telegram_id, server_id, server_name, server_type, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (telegram_id, server_id, server_name, server_type, status))
                conn.commit()
                return True
        except Exception as e:
            print(f"خطأ في إضافة السيرفر: {e}")
            return False
    
    def get_user_servers(self, telegram_id: int) -> List[Dict[str, Any]]:
        """الحصول على سيرفرات المستخدم"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM servers WHERE telegram_id = ?', (telegram_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"خطأ في الحصول على السيرفرات: {e}")
            return []
    
    def add_transaction(self, telegram_id: int, transaction_type: str, 
                       amount: float, description: str) -> bool:
        """إضافة معاملة جديدة"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transactions 
                    (telegram_id, transaction_type, amount, description)
                    VALUES (?, ?, ?, ?)
                ''', (telegram_id, transaction_type, amount, description))
                conn.commit()
                return True
        except Exception as e:
            print(f"خطأ في إضافة المعاملة: {e}")
            return False
    
    def get_user_transactions(self, telegram_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """الحصول على معاملات المستخدم"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE telegram_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (telegram_id, limit))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"خطأ في الحصول على المعاملات: {e}")
            return []

# إنشاء كائن إدارة قاعدة البيانات
db = DatabaseManager()

