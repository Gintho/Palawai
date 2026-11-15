"""Chargement de la config des spots et récupération des prévisions Open-Meteo."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPOTS_FILE = ROOT / "_bmad/custom/agents/surf-forecaster/surf-forecaster-sidecar/spots.yaml"

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
UA = {"User-Agent": "surf-forecast-bot/1.0"}


def load_config(path: Path = SPOTS_FILE) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_json(url: str, params: dict, attempts: int = 3) -> dict:
    """GET JSON avec nouvelles tentatives (Open-Meteo a parfois des ratés réseau)."""
    full = f"{url}?{urllib.parse.urlencode(params)}"
    for i in range(attempts):
        try:
            req = urllib.request.Request(full, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(5 * 2 ** i)  # 5 s puis 10 s


MARINE_VARS = ("wave_height,wave_period,wave_direction,swell_wave_height,"
               "swell_wave_period,swell_wave_direction,sea_surface_temperature")
WIND_VARS = "wind_speed_10m,wind_direction_10m,wind_gusts_10m"


def _coords(points: list[dict]) -> dict:
    return {"latitude": ",".join(str(p["lat"]) for p in points),
            "longitude": ",".join(str(p["lon"]) for p in points)}


def fetch_all(spots: list[dict], timezone: str, days: int = 2) -> dict[str, dict]:
    """Toutes les prévisions en 2 requêtes (Open-Meteo accepte plusieurs coordonnées)."""
    sea_pts = [s.get("forecast_point", {"lat": s["lat"], "lon": s["lon"]}) for s in spots]
    common = {"timezone": timezone, "forecast_days": days}
    marine = _get_json(MARINE_URL, {**_coords(sea_pts), "hourly": MARINE_VARS, **common})
    weather = _get_json(WEATHER_URL, {**_coords(spots), "hourly": WIND_VARS,
                                      "wind_speed_unit": "kmh", **common})
    if isinstance(marine, dict):  # un seul spot -> objet au lieu d'une liste
        marine, weather = [marine], [weather]
    return {s["id"]: merge(m, w) for s, m, w in zip(spots, marine, weather)}


def merge(marine: dict, weather: dict) -> dict:
    m, w = marine["hourly"], weather["hourly"]
    wind_by_time = {t: i for i, t in enumerate(w["time"])}
    hours = []
    for i, t in enumerate(m["time"]):
        j = wind_by_time.get(t)
        hours.append({
            "time": t,
            "wave_height": m["wave_height"][i],
            "wave_period": m["wave_period"][i],
            "wave_direction": m["wave_direction"][i],
            "swell_height": m.get("swell_wave_height", [None] * len(m["time"]))[i],
            "swell_period": m.get("swell_wave_period", [None] * len(m["time"]))[i],
            "wind_speed": w["wind_speed_10m"][j] if j is not None else None,
            "wind_direction": w["wind_direction_10m"][j] if j is not None else None,
            "wind_gusts": w["wind_gusts_10m"][j] if j is not None else None,
        })
    sst = [x for x in m.get("sea_surface_temperature", []) if x is not None]
    return {"hourly": hours, "sea_temp": round(sum(sst) / len(sst), 1) if sst else None}
