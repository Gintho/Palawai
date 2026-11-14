"""Construction du message Telegram (HTML)."""

from __future__ import annotations

from datetime import date, timedelta
from html import escape

from .scoring import HourScore, best_window, compass, score_hour, verdict

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août",
        "sept.", "oct.", "nov.", "déc."]


def fr_date(d: date) -> str:
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]}"


def day_scores(forecast: dict, spot: dict, criteria: dict, day: date) -> list[HourScore]:
    start, end = criteria["daylight_hours"]
    prefix = day.isoformat()
    out = []
    for h in forecast["hourly"]:
        if not h["time"].startswith(prefix):
            continue
        hour = int(h["time"][11:13])
        if start <= hour <= end and h["wave_height"] is not None:
            out.append(score_hour(h, spot, criteria))
    return out


def wetsuit(sst: float | None) -> str:
    if sst is None:
        return ""
    if sst >= 22:
        return "short / lycra"
    if sst >= 19:
        return "shorty ou 2 mm"
    if sst >= 16:
        return "3/2 mm"
    if sst >= 13:
        return "4/3 mm + chaussons"
    return "5/4 mm, chaussons, cagoule"


def marin_then_tramontane(scores: list[HourScore]) -> bool:
    """Détecte la rotation onshore → offshore avec houle encore présente."""
    seen_onshore = False
    for s in scores:
        if s.wind_label.startswith("onshore") and s.wind_speed >= 12:
            seen_onshore = True
        elif seen_onshore and s.wind_label.startswith("offshore") and s.wave_height >= 0.8:
            return True
    return False


def build_report(config: dict, forecasts: dict[str, dict], today: date) -> str:
    criteria = config["criteria"]
    lines = [f"🏄 <b>Surf Forecast Palavas / Carnon</b>", f"📅 {fr_date(today)}", ""]

    days = [(today, "AUJOURD'HUI"), (today + timedelta(days=1), "DEMAIN")]
    summary_today: list[tuple[float, str, tuple | None]] = []

    for day, label in days:
        lines.append(f"━━━ <b>{label}</b> — {fr_date(day)} ━━━")
        ranked = []
        for spot in config["spots"]:
            fc = forecasts.get(spot["id"])
            if not fc:
                continue
            scores = day_scores(fc, spot, criteria, day)
            if not scores:
                continue
            best = max(scores, key=lambda s: s.score)
            ranked.append((best.score, spot, best, best_window(scores), scores))
        ranked.sort(key=lambda r: r[0], reverse=True)

        if not ranked:
            lines += ["Pas de données disponibles.", ""]
            continue

        for score, spot, best, window, scores in ranked:
            emoji, _ = verdict(score, criteria)
            gust = f" (raf. {best.wind_gusts:.0f})" if best.wind_gusts else ""
            lines.append(f"{emoji} <b>{escape(spot['name'])}</b> — {score:.1f}/10")
            lines.append(
                f"   🌊 {best.wave_height:.1f} m · {best.wave_period:.0f} s ({best.period_label})"
                f" · {compass(best.wave_direction)}"
            )
            lines.append(
                f"   💨 {best.wind_speed:.0f} km/h{gust} {compass(best.wind_direction)}"
                f" · {best.wind_label}"
            )
            if window:
                slot = window[0] if window[0] == window[1] else f"{window[0]} → {window[1]}"
                lines.append(f"   ⏰ Créneau : {slot}")
            if marin_then_tramontane(scores):
                lines.append("   ✨ Rotation Marin → Tramontane : fenêtre à saisir !")

        top_score, top_spot, top_best, top_window, _ = ranked[0]
        emoji, label_v = verdict(top_score, criteria)
        if day == today:
            summary_today.append((top_score, top_spot["name"], top_window))
        lines.append("")
        lines.append(f"👉 <b>Verdict : {emoji} {label_v}</b>")
        if top_score >= 4:
            when = ""
            if top_window:
                when = f" ({top_window[0]})" if top_window[0] == top_window[1] \
                    else f" ({top_window[0]}-{top_window[1]})"
            lines.append(f"   Meilleur spot : {escape(top_spot['name'])}{when}")
        lines.append("")

    sst = next((f["sea_temp"] for f in forecasts.values() if f.get("sea_temp")), None)
    if sst:
        lines.append(f"🌡️ Eau : {sst:.0f}°C → combi {wetsuit(round(sst))}")
    if any(f["hourly"] and max((h["wave_height"] or 0) for h in f["hourly"]) > 2.0
           for f in forecasts.values()):
        lines.append("⚠️ Gros : attention aux digues, épis et courants.")
    lines.append("<i>Données Open-Meteo · score 0-10 (taille × période × direction × vent)</i>")
    return "\n".join(lines)
