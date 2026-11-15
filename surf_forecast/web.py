"""Application WSGI (Vercel) : webhook Telegram et branchement du webhook.

Routes :
  POST /api/telegram          webhook Telegram (« surf » → forecast)
  GET  /api/setup?key=...     enregistre le webhook auprès de Telegram (key = WEBHOOK_SECRET)

Pas d'envoi automatique : le forecast n'est envoyé que quand l'utilisateur écrit « surf ».
"""

from __future__ import annotations

import hmac
import json
import os
from urllib.parse import parse_qs

from . import service, telegram

TRIGGERS = {"surf", "/surf", "forecast", "/forecast", "vagues", "go"}
HELP = ("🏄 Salut, c'est Kai !\n\n"
        "Envoie <b>surf</b> et je te donne le forecast de Palavas / Carnon / Maguelone "
        "pour aujourd'hui et demain, avec mon verdict.")


def _same(a: str, b: str) -> bool:
    return bool(a) and hmac.compare_digest(a.encode(), b.encode())


def handle_telegram(headers: dict, body: bytes) -> tuple[int, dict]:
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if not _same(secret, headers.get("x-telegram-bot-api-secret-token", "")):
        return 401, {"ok": False}
    update = json.loads(body or b"{}")
    msg = update.get("message") or update.get("edited_message") or {}
    chat_id = str(msg.get("chat", {}).get("id", ""))
    text = (msg.get("text") or "").strip().lower().split("@")[0]

    allowed = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not chat_id or (allowed and chat_id not in allowed.split(",")):
        return 200, {"ok": True, "ignored": True}

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    if text in TRIGGERS:
        telegram.call(token, "sendChatAction", {"chat_id": chat_id, "action": "typing"})
        service.send_forecast(chat_id)
    else:
        telegram.send(token, chat_id, HELP)
    return 200, {"ok": True}


def handle_setup(query: dict, host: str) -> tuple[int, dict]:
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if not _same(secret, query.get("key", [""])[0]):
        return 401, {"ok": False}
    host = os.environ.get("VERCEL_PROJECT_PRODUCTION_URL") or host
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    telegram.call(token, "setWebhook", {
        "url": f"https://{host}/api/telegram", "secret_token": secret,
        "allowed_updates": ["message", "edited_message"], "drop_pending_updates": True,
    })
    telegram.call(token, "setMyCommands", {"commands": [
        {"command": "surf", "description": "Forecast surf du jour et de demain"}]})
    info = telegram.call(token, "getWebhookInfo", {})["result"]
    return 200, {"ok": True, "webhook_url": info.get("url"),
                 "pending": info.get("pending_update_count"),
                 "last_error": info.get("last_error_message")}


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/").rstrip("/") or "/"
    method = environ.get("REQUEST_METHOD", "GET")
    headers = {k[5:].replace("_", "-").lower(): v for k, v in environ.items()
               if k.startswith("HTTP_")}
    try:
        if path == "/api/telegram" and method == "POST":
            length = int(environ.get("CONTENT_LENGTH") or 0)
            status, body = handle_telegram(headers, environ["wsgi.input"].read(length))
        elif path == "/api/setup":
            status, body = handle_setup(parse_qs(environ.get("QUERY_STRING", "")),
                                        headers.get("host", ""))
        else:
            status, body = 200, {"ok": True, "service": "Kai surf forecast"}
    except Exception as exc:  # toujours répondre, sinon Telegram renvoie en boucle
        status, body = 500, {"ok": False, "error": str(exc)}
    data = json.dumps(body).encode()
    reasons = {200: "OK", 401: "Unauthorized", 500: "Internal Server Error"}
    start_response(f"{status} {reasons.get(status, '')}",
                   [("Content-Type", "application/json"), ("Content-Length", str(len(data)))])
    return [data]
