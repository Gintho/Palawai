"""Fonctions partagées par la CLI, le webhook Telegram et le cron Vercel."""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from . import data, report, telegram


def forecast_text() -> str:
    config = data.load_config()
    tz = config["region"]["timezone"]
    forecasts = data.fetch_all(config["spots"], tz)
    return report.build_report(config, forecasts, datetime.now(ZoneInfo(tz)).date())


def send_forecast(chat_id: str | None = None) -> str:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = chat_id or os.environ["TELEGRAM_CHAT_ID"]
    try:
        text = forecast_text()
    except Exception as exc:
        text = f"😕 Impossible de récupérer les prévisions pour l'instant ({exc}). Réessaie dans quelques minutes."
    telegram.send(token, chat_id, text)
    return text
