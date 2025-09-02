import json
import requests
import telebot
import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from urllib.parse import urljoin

with open(f"{BASE_DIR}/config.json","r") as f:
  cfg = json.load(f)

BOT_TOKEN = cfg.get("TELEGRAM_TOKEN")
PTERO_URL = cfg.get("PTERO_URL").rstrip("/")
PTERO_APP_KEY = cfg.get("PTERO_APP_KEY")
PTERO_CLIENT_KEY = cfg.get("PTERO_CLIENT_KEY")
CTRL_URL = cfg.get("CTRL_URL").rstrip("/")
CTRL_KEY = cfg.get("CTRL_KEY")

bot = telebot.TeleBot(BOT_TOKEN)

def ptero_headers(app=True):
  key = PTERO_APP_KEY if app else PTERO_CLIENT_KEY
  return {
    "Authorization": f"Bearer {key}",
    "Accept": "application/json",
    "Content-Type": "application/json"
  }

def ctrl_headers():
  return {
    "Authorization": f"Bearer {CTRL_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
  }

def safe_get(url, headers=None, params=None):
  try:
    r = requests.get(url, headers=headers or {}, params=params, timeout=15)
    return r.status_code, r.json() if r.content else {}
  except Exception as e:
    return 0, {"error": str(e)}

def safe_post(url, headers=None, json_data=None):
  try:
    r = requests.post(url, headers=headers or {}, json=json_data or {}, timeout=20)
    return r.status_code, r.json() if r.content else {}
  except Exception as e:
    return 0, {"error": str(e)}

def safe_delete(url, headers=None):
  try:
    r = requests.delete(url, headers=headers or {}, timeout=15)
    return r.status_code, r.json() if r.content else {"status": r.status_code}
  except Exception as e:
    return 0, {"error": str(e)}

@bot.message_handler(commands=["start","help"])
def cmd_start(m):
  txt = ("أهلا 👋\n"
  "/ptero_servers - جلب كل السيرفرات (Application API)\n"
  "/ptero_server <id> - تفاصيل سيرفر\n"
  "/ptero_power <id> <start|stop|restart> - إرسال إشارة طاقة للسيرفر\n"
  "/ctrl_servers - جلب سيرفرات CtrlPanel\n"
  "/ctrl_products - جلب منتجات المتجر\n"
  "/ctrl_create_voucher <code>|<amount> - إنشاء فواتشر (مثال: /ctrl_create_voucher CODE123|10)\n"
  "/ctrl_tickets_create <subject>|<message> - إنشاء تذكرة\n"
  "/ctrl_payments - جلب المدفوعات\n"
  "اكتب الأمر مع المعاملات كما في الأمثلة")
  bot.reply_to(m, txt)

@bot.message_handler(commands=["ptero_servers"])
def cmd_ptero_servers(m):
  url = urljoin(PTERO_URL, "/api/application/servers")
  status, data = safe_get(url, headers=ptero_headers(app=True))
  if status == 200:
    items = data.get("data") or data.get("servers") or data
    if not items:
      bot.reply_to(m, "مفيش سيرفرات أو لم يتم جلبهم")
      return
    lines = []
    for s in items:
      sid = s.get("attributes",{}).get("id") or s.get("id") or s.get("identifier")
      name = s.get("attributes",{}).get("name") or s.get("name")
      lines.append(f"{sid} • {name}")
    bot.reply_to(m, "<b>Pterodactyl Servers:</b>\n" + "\n".join(lines))
  else:
    bot.reply_to(m, f"خطأ: {status}\n{json.dumps(data, ensure_ascii=False)}")

@bot.message_handler(commands=["ptero_server"])
def cmd_ptero_server(m):
  parts = m.text.split()
  if len(parts) < 2:
    bot.reply_to(m, "استخدم: /ptero_server <id>")
    return
  sid = parts[1]
  url = urljoin(PTERO_URL, f"/api/application/servers/{sid}")
  status, data = safe_get(url, headers=ptero_headers(app=True))
  if status == 200:
    attrs = data.get("attributes") or data.get("server") or data
    bot.reply_to(m, "<b>Server Details</b>\n" + json.dumps(attrs, indent=2, ensure_ascii=False))
  else:
    bot.reply_to(m, f"خطأ: {status}\n{json.dumps(data, ensure_ascii=False)}")

@bot.message_handler(commands=["ptero_power"])
def cmd_ptero_power(m):
  parts = m.text.split()
  if len(parts) < 3:
    bot.reply_to(m, "استخدم: /ptero_power <id> <start|stop|restart>")
    return
  sid = parts[1]
  action = parts[2].lower()
  if action not in ("start","stop","restart"):
    bot.reply_to(m, "action لازم تكون start أو stop أو restart")
    return
  url = urljoin(PTERO_URL, f"/api/client/servers/{sid}/power")
  payload = {"signal": "start" if action=="start" else ("stop" if action=="stop" else "restart")}
  status, data = safe_post(url, headers=ptero_headers(app=False), json_data=payload)
  if status in (200,204):
    bot.reply_to(m, "تم إرسال الإشارة بنجاح")
  else:
    bot.reply_to(m, f"خطأ: {status}\n{json.dumps(data, ensure_ascii=False)}")

@bot.message_handler(commands=["ctrl_servers"])
def cmd_ctrl_servers(m):
  url = urljoin(CTRL_URL, "/api/servers")
  status, data = safe_get(url, headers=ctrl_headers())
  if status == 200:
    items = data.get("data") or data
    if isinstance(items, dict) and "servers" in items:
      items = items["servers"]
    lines = []
    for s in items:
      sid = s.get("id") or s.get("identifier") or s.get("_id")
      name = s.get("name") or s.get("hostname") or s.get("description")
      lines.append(f"{sid} • {name}")
    bot.reply_to(m, "<b>CtrlPanel Servers:</b>\n" + ("\n".join(lines) if lines else "لا توجد سيرفرات"))
  else:
    bot.reply_to(m, f"خطأ: {status}\n{json.dumps(data, ensure_ascii=False)}")

@bot.message_handler(commands=["ctrl_products"])
def cmd_ctrl_products(m):
  url = urljoin(CTRL_URL, "/api/products")
  status, data = safe_get(url, headers=ctrl_headers())
  if status == 200:
    items = data.get("data") or data
    lines = []
    for p in items:
      pid = p.get("id") or p.get("_id") or p.get("identifier")
      name = p.get("name") or p.get("title")
      price = p.get("price") or p.get("cost") or p.get("monthly_price")
      lines.append(f"{pid} • {name} • {price}")
    bot.reply_to(m, "<b>Products:</b>\n" + ("\n".join(lines) if lines else "لا توجد منتجات"))
  else:
    bot.reply_to(m, f"خطأ: {status}\n{json.dumps(data, ensure_ascii=False)}")

@bot.message_handler(commands=["ctrl_create_voucher"])
def cmd_ctrl_create_voucher(m):
  txt = m.text.partition(" ")[2]
  if "|" not in txt:
    bot.reply_to(m, "استخدم: /ctrl_create_voucher <code>|<amount>")
    return
  code, amount = [x.strip() for x in txt.split("|",1)]
  try:
    amount_val = float(amount)
  except:
    bot.reply_to(m, "المبلغ لازم يكون رقم")
    return
  url = urljoin(CTRL_URL, "/api/vouchers")
  payload = {"code": code, "amount": amount_val}
  status, data = safe_post(url, headers=ctrl_headers(), json_data=payload)
  if status in (200,201):
    bot.reply_to(m, "تم إنشاء الفاتشر ✅\n" + json.dumps(data, ensure_ascii=False))
  else:
    bot.reply_to(m, f"خطأ: {status}\n{json.dumps(data, ensure_ascii=False)}")

@bot.message_handler(commands=["ctrl_tickets_create"])
def cmd_ctrl_tickets_create(m):
  txt = m.text.partition(" ")[2]
  if "|" not in txt:
    bot.reply_to(m, "استخدم: /ctrl_tickets_create <subject>|<message>")
    return
  subject, message = [x.strip() for x in txt.split("|",1)]
  url = urljoin(CTRL_URL, "/api/tickets")
  payload = {"subject": subject, "message": message}
  status, data = safe_post(url, headers=ctrl_headers(), json_data=payload)
  if status in (200,201):
    bot.reply_to(m, "تم إنشاء التذكرة ✅\n" + json.dumps(data, ensure_ascii=False))
  else:
    bot.reply_to(m, f"خطأ: {status}\n{json.dumps(data, ensure_ascii=False)}")

@bot.message_handler(commands=["ctrl_payments"])
def cmd_ctrl_payments(m):
  url = urljoin(CTRL_URL, "/api/payments")
  status, data = safe_get(url, headers=ctrl_headers())
  if status == 200:
    items = data.get("data") or data
    bot.reply_to(m, "<b>Payments:</b>\n" + json.dumps(items, indent=2, ensure_ascii=False)[:4000])
  else:
    bot.reply_to(m, f"خطأ: {status}\n{json.dumps(data, ensure_ascii=False)}")

@bot.message_handler(func=lambda m: True)
def fallback(m):
  txt = ("مش فاهم الأمر ده. اكتب /help لمعرفة الأوامر المتاحة.")
  bot.reply_to(m, txt)

os.system("clear")
print("bot starting")
bot.infinity_polling()