# دليل نشر بوت تيليجرام Nexo

## نظرة عامة

هذا الدليل يوضح كيفية نشر وتشغيل بوت تيليجرام Nexo على خادم إنتاج أو VPS.

## متطلبات النظام

### الحد الأدنى للمتطلبات
- **نظام التشغيل:** Ubuntu 20.04+ أو CentOS 8+
- **الذاكرة:** 512 MB RAM (مُوصى بـ 1GB+)
- **التخزين:** 1 GB مساحة فارغة
- **Python:** الإصدار 3.7 أو أحدث
- **الشبكة:** اتصال إنترنت مستقر

### المتطلبات المُوصى بها
- **الذاكرة:** 2 GB RAM
- **المعالج:** 2 CPU cores
- **التخزين:** 5 GB SSD
- **Firewall:** فتح المنافذ المطلوبة

## خطوات النشر

### 1. تحضير الخادم

#### تحديث النظام
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

#### تثبيت Python و Git
```bash
# Ubuntu/Debian
sudo apt install python3 python3-pip git -y

# CentOS/RHEL
sudo yum install python3 python3-pip git -y
```

### 2. تحميل المشروع

```bash
# إنشاء مجلد للمشروع
mkdir -p /opt/nexo-bot
cd /opt/nexo-bot

# تحميل ملفات المشروع (استبدل بالرابط الصحيح)
git clone <your-repository-url> .

# أو رفع الملفات يدوياً
# scp -r nexo_telegram_bot/ user@server:/opt/nexo-bot/
```

### 3. تثبيت المتطلبات

```bash
# تثبيت المكتبات المطلوبة
pip3 install -r requirements.txt

# التحقق من التثبيت
python3 -c "import telebot; print('✅ pyTelegramBotAPI installed')"
python3 -c "import requests; print('✅ requests installed')"
```

### 4. إعداد متغيرات البيئة

#### إنشاء ملف .env
```bash
cp .env.example .env
nano .env
```

#### تعديل الإعدادات
```env
# توكن البوت من BotFather
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# روابط المنصات
CTRLPANEL_BASE_URL=https://nexo.midoghanam.site
PTERODACTYL_BASE_URL=https://panal.nexo.midoghanam.site

# قاعدة البيانات
DATABASE_PATH=/opt/nexo-bot/bot_database.db

# معرفات المديرين
ADMIN_USER_IDS=123456789,987654321
```

### 5. اختبار البوت

```bash
# تشغيل الاختبارات
python3 test_bot.py

# اختبار تشغيل البوت (إيقاف بـ Ctrl+C)
python3 start_bot.py
```

### 6. إعداد خدمة النظام (Systemd)

#### إنشاء ملف الخدمة
```bash
sudo nano /etc/systemd/system/nexo-bot.service
```

#### محتوى ملف الخدمة
```ini
[Unit]
Description=Nexo Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nexo-bot
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 /opt/nexo-bot/start_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### تفعيل وتشغيل الخدمة
```bash
# إعادة تحميل systemd
sudo systemctl daemon-reload

# تفعيل الخدمة للتشغيل التلقائي
sudo systemctl enable nexo-bot

# بدء الخدمة
sudo systemctl start nexo-bot

# التحقق من الحالة
sudo systemctl status nexo-bot
```

### 7. إدارة الخدمة

```bash
# إيقاف البوت
sudo systemctl stop nexo-bot

# إعادة تشغيل البوت
sudo systemctl restart nexo-bot

# عرض السجلات
sudo journalctl -u nexo-bot -f

# عرض آخر 100 سطر من السجلات
sudo journalctl -u nexo-bot -n 100
```

## إعداد Nginx (اختياري)

إذا كنت تريد إضافة واجهة ويب أو API endpoints:

### تثبيت Nginx
```bash
sudo apt install nginx -y
```

### إعداد Nginx
```bash
sudo nano /etc/nginx/sites-available/nexo-bot
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /bot-status {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## المراقبة والصيانة

### مراقبة الأداء

#### استخدام htop
```bash
sudo apt install htop -y
htop
```

#### مراقبة استهلاك الذاكرة
```bash
free -h
```

#### مراقبة مساحة القرص
```bash
df -h
```

### النسخ الاحتياطي

#### نسخ احتياطي لقاعدة البيانات
```bash
# إنشاء مجلد النسخ الاحتياطية
mkdir -p /opt/backups

# نسخ قاعدة البيانات
cp /opt/nexo-bot/bot_database.db /opt/backups/bot_database_$(date +%Y%m%d_%H%M%S).db
```

#### نسخ احتياطي تلقائي (Cron)
```bash
# تحرير crontab
crontab -e

# إضافة مهمة نسخ احتياطي يومية في الساعة 2:00 صباحاً
0 2 * * * cp /opt/nexo-bot/bot_database.db /opt/backups/bot_database_$(date +\%Y\%m\%d_\%H\%M\%S).db
```

### تحديث البوت

```bash
# إيقاف البوت
sudo systemctl stop nexo-bot

# نسخ احتياطي
cp bot_database.db bot_database_backup.db

# تحديث الكود
git pull origin main
# أو رفع الملفات الجديدة

# تثبيت المتطلبات الجديدة (إن وجدت)
pip3 install -r requirements.txt

# اختبار التحديث
python3 test_bot.py

# إعادة تشغيل البوت
sudo systemctl start nexo-bot
```

## استكشاف الأخطاء

### مشاكل شائعة

#### البوت لا يبدأ
```bash
# التحقق من السجلات
sudo journalctl -u nexo-bot -n 50

# التحقق من متغيرات البيئة
python3 -c "import os; print('BOT_TOKEN:', os.getenv('BOT_TOKEN', 'NOT SET'))"

# اختبار يدوي
python3 start_bot.py
```

#### مشاكل الاتصال بـ APIs
```bash
# اختبار الاتصال
curl -I https://nexo.midoghanam.site
curl -I https://panal.nexo.midoghanam.site

# التحقق من DNS
nslookup nexo.midoghanam.site
```

#### مشاكل قاعدة البيانات
```bash
# التحقق من صلاحيات الملف
ls -la bot_database.db

# إعادة إنشاء قاعدة البيانات
rm bot_database.db
python3 -c "from database import db; print('Database recreated')"
```

### ملفات السجلات

- **سجلات النظام:** `/var/log/syslog`
- **سجلات البوت:** `journalctl -u nexo-bot`
- **سجلات التطبيق:** `bot.log` في مجلد المشروع

## الأمان

### إعدادات الأمان الأساسية

```bash
# تحديث كلمة مرور root
sudo passwd root

# إعداد firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# تعطيل تسجيل الدخول بـ root عبر SSH
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
sudo systemctl restart ssh
```

### حماية ملف .env
```bash
# تقييد الصلاحيات
chmod 600 .env
chown root:root .env
```

## الأداء والتحسين

### تحسين Python
```bash
# استخدام Python المحسن
pip3 install --upgrade pip setuptools wheel
```

### تحسين قاعدة البيانات
```bash
# تنظيف قاعدة البيانات دورياً
sqlite3 bot_database.db "VACUUM;"
```

## الدعم والمساعدة

### معلومات مفيدة للدعم
```bash
# معلومات النظام
uname -a
python3 --version
pip3 --version

# حالة الخدمة
sudo systemctl status nexo-bot

# استهلاك الموارد
ps aux | grep python
```

### جهات الاتصال
- **المطور:** [معلومات الاتصال]
- **الوثائق:** [رابط الوثائق]
- **المستودع:** [رابط GitHub]

---

**ملاحظة:** تأكد من تحديث هذا الدليل عند إجراء تغييرات على البوت أو إضافة ميزات جديدة.

