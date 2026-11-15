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


def call(token: str, method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.load(r)
    if not resp.get("ok"):
        raise RuntimeError(f"Telegram error: {resp}")
    return resp


def send(token: str, chat_id: str, text: str) -> None:
    for chunk in split_message(text):
        call(token, "sendMessage", {"chat_id": chat_id, "text": chunk, "parse_mode": "HTML",
                                    "disable_web_page_preview": True})
