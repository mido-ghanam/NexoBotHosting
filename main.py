from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, KeyboardMarkup
import requests, telebot, sys, os
from urllib.parse import urljoin
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import utils

cfg = utils.json.jsonLoad(f"config.json", getKeys=["TELEGRAM_BOT_TOKEN", "CTRL_URL", "PTERO_URL"])

nexobot = telebot.TeleBot(cfg.get("TELEGRAM_BOT_TOKEN"))

APIs = {
  "PTERO": {
    "BASE_URL": cfg.get("PTERO_URL"),
  },
  "CTRL": {
    "BASE_URL": cfg.get("CTRL_URL"),
  },
}

@nexobot.message_handler(commands=["start", "help"])
def send_welcome(message):
  TEXT = f"""
اهلا بيك {message.from_user.first_name} في بوت منصة Nexo.
يمكنك إدارة حسابك وسيرفراتك من خلال البوت هنا
اختر من الأزرار في الأسفل
"""
  markup = KeyboardMarkup(resize_keyboard=True)
  users = utils.json.jsonLoad(f"bot.json", getKeys=["users"])
  if str(message.from_user.id) not in users.keys() or not users.get(str(message.from_user.id, {})).get("API_KEY", ""):
    TEXT += f"\n\nقم بتسجيل الدخول باستخدام /login"
    markup.add(KeyboardButton("/login"))
  nexobot.reply_to(message, text=TEXT, reply_markup=markup)

nexobot.infinity_polling()