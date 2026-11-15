"""Webhook Telegram : envoie « surf » au bot pour recevoir le forecast."""

import hmac
import json
import os
from http.server import BaseHTTPRequestHandler

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _common import reply  # noqa: E402
from surf_forecast import service, telegram  # noqa: E402

TRIGGERS = {"surf", "/surf", "forecast", "/forecast", "vagues", "go"}
HELP = ("🏄 Salut, c'est Kai !\n\n"
        "Envoie <b>surf</b> et je te donne le forecast de Palavas / Carnon / Maguelone "
        "pour aujourd'hui et demain, avec mon verdict.\n"
        "Tu reçois aussi le forecast automatiquement chaque matin.")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        secret = os.environ.get("WEBHOOK_SECRET", "")
        got = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not secret or not hmac.compare_digest(secret, got):
            return reply(self, 401, {"ok": False})

        length = int(self.headers.get("Content-Length", 0))
        update = json.loads(self.rfile.read(length) or b"{}")
        msg = update.get("message") or update.get("edited_message") or {}
        chat_id = str(msg.get("chat", {}).get("id", ""))
        text = (msg.get("text") or "").strip().lower().split("@")[0]

        allowed = os.environ.get("TELEGRAM_CHAT_ID", "")
        if not chat_id or (allowed and chat_id not in allowed.split(",")):
            return reply(self, 200, {"ok": True, "ignored": True})

        token = os.environ["TELEGRAM_BOT_TOKEN"]
        if text in TRIGGERS:
            telegram.call(token, "sendChatAction", {"chat_id": chat_id, "action": "typing"})
            service.send_forecast(chat_id)
        else:
            telegram.send(token, chat_id, HELP)
        return reply(self, 200, {"ok": True})

    def do_GET(self):
        return reply(self, 200, {"ok": True, "service": "surf-forecast webhook"})
