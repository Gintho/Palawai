"""Cron Vercel quotidien : envoie le forecast du matin."""

import hmac
import os
from http.server import BaseHTTPRequestHandler

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _common import reply  # noqa: E402
from surf_forecast import service  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        expected = f"Bearer {os.environ.get('CRON_SECRET', '')}"
        if not os.environ.get("CRON_SECRET") or not hmac.compare_digest(
                expected, self.headers.get("Authorization", "")):
            return reply(self, 401, {"ok": False})
        service.send_forecast()
        return reply(self, 200, {"ok": True})
