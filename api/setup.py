"""Branche le webhook Telegram : GET /api/setup?key=<WEBHOOK_SECRET>"""

import hmac
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _common import reply  # noqa: E402
from surf_forecast import telegram  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        secret = os.environ.get("WEBHOOK_SECRET", "")
        key = parse_qs(urlparse(self.path).query).get("key", [""])[0]
        if not secret or not hmac.compare_digest(secret, key):
            return reply(self, 401, {"ok": False})
        host = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL") or self.headers.get("Host")
        token = os.environ["TELEGRAM_BOT_TOKEN"]
        try:
            hook = telegram.call(token, "setWebhook", {
                "url": f"https://{host}/api/telegram", "secret_token": secret,
                "allowed_updates": ["message", "edited_message"], "drop_pending_updates": True,
            })
            telegram.call(token, "setMyCommands", {"commands": [
                {"command": "surf", "description": "Forecast surf du jour et de demain"},
            ]})
            info = telegram.call(token, "getWebhookInfo", {})
        except Exception as exc:
            return reply(self, 500, {"ok": False, "error": str(exc)})
        return reply(self, 200, {"ok": True, "setWebhook": hook, "info": info["result"]})
