"""python -m surf_forecast [--dry-run]

Récupère les prévisions, note chaque spot et envoie le forecast sur Telegram.
Variables d'environnement : TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from . import data, report, telegram


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Forecast surf Palavas / Carnon → Telegram")
    parser.add_argument("--dry-run", action="store_true", help="affiche le message sans l'envoyer")
    args = parser.parse_args(argv)

    config = data.load_config()
    tz = config["region"]["timezone"]
    today = datetime.now(ZoneInfo(tz)).date()

    try:
        forecasts = data.fetch_all(config["spots"], tz)
    except Exception as exc:
        print(f"Aucune prévision récupérée : {exc}", file=sys.stderr)
        return 1

    text = report.build_report(config, forecasts, today)
    print(text)

    if args.dry_run:
        return 0
    token, chat_id = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID manquants.", file=sys.stderr)
        return 2
    telegram.send(token, chat_id, text)
    print("✅ Envoyé sur Telegram")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
