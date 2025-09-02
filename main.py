from urllib.parse import urljoin
import json, requests, telebot, sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(f"{BASE_DIR}/config.json","r") as f:
  cfg = json.load(f)

nexobot = telebot.TeleBot(cfg.get("TELEGRAM_BOT_TOKEN"))

APIs = {
  "PTERO_URL": cfg.get("PTERO_URL"),
  "CTRL_URL": cfg.get("CTRL_URL"),
}