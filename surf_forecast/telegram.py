"""Envoi du message via l'API Bot Telegram."""

from __future__ import annotations

import json
import urllib.request

MAX_LEN = 4096


def split_message(text: str, limit: int = MAX_LEN) -> list[str]:
    chunks, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = ""
        current += line + "\n"
    if current.strip():
        chunks.append(current)
    return chunks


def send(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for chunk in split_message(text):
        body = json.dumps({
            "chat_id": chat_id, "text": chunk, "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.load(r)
        if not resp.get("ok"):
            raise RuntimeError(f"Telegram error: {resp}")
