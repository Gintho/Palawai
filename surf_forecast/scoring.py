"""Notation des conditions de surf (0 → 10) selon les critères de spots.yaml."""

from __future__ import annotations

from dataclasses import dataclass


def angle_diff(a: float, b: float) -> float:
    """Écart angulaire absolu entre deux directions (0-180°)."""
    d = abs((a - b) % 360)
    return 360 - d if d > 180 else d


def in_window(direction: float, window: list[float]) -> bool:
    lo, hi = window
    if lo <= hi:
        return lo <= direction <= hi
    return direction >= lo or direction <= hi


COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
COMPASS_FR = {"SSW": "SSO", "SW": "SO", "WSW": "OSO", "W": "O", "WNW": "ONO",
              "NW": "NO", "NNW": "NNO"}


def compass(deg: float | None) -> str:
    if deg is None:
        return "?"
    c = COMPASS[int((deg % 360) / 22.5 + 0.5) % 16]
    return COMPASS_FR.get(c, c)


def height_score(h: float, spot: dict) -> float:
    lo, hi = spot["best_height"]
    if h < 0.3:
        return 0.0
    if h < spot.get("min_height", 0.5):
        return 2.0
    if h < lo:
        # interpolation 5 → 10 entre min_height et le bas de best_height
        m = spot.get("min_height", 0.5)
        return 5.0 + 5.0 * (h - m) / max(lo - m, 0.01)
    if h <= hi:
        return 10.0
    # trop gros pour la Méditerranée : décroît, ~4 à hi + 1.5 m
    return max(3.0, 10.0 - 4.0 * (h - hi))


def period_factor(period: float, criteria: dict) -> tuple[float, str]:
    for step in criteria["period"]:
        if period < step["max"]:
            return step["factor"], step["label"]
    last = criteria["period"][-1]
    return last["factor"], last["label"]


def direction_factor(direction: float, spot: dict) -> float:
    if not in_window(direction, spot["swell_window"]):
        return 0.2
    lo, hi = spot["swell_window"]
    half = max(angle_diff(lo, spot["best_swell_dir"]), angle_diff(hi, spot["best_swell_dir"]))
    d = angle_diff(direction, spot["best_swell_dir"])
    return 1.0 - 0.4 * min(d / max(half, 1), 1.0)  # 1.0 au centre → 0.6 au bord


def wind_factor(speed: float, direction: float, spot: dict, criteria: dict) -> tuple[float, str]:
    w = criteria["wind"]
    if speed < w["glassy_below_kmh"]:
        return 1.0, "glassy"
    d = angle_diff(direction, spot["offshore_wind"])
    if d <= 45:  # offshore
        if speed <= 30:
            return 1.0, "offshore"
        if speed <= w["offshore_too_strong_kmh"]:
            return 0.8, "offshore fort"
        return 0.5, "offshore violent"
    if d <= 120:  # side-shore
        if speed <= 15:
            return 0.85, "side-shore"
        if speed <= 25:
            return 0.65, "side-shore"
        return 0.45, "side-shore fort"
    # onshore
    if speed <= 12:
        return 0.85, "onshore léger"
    if speed <= w["onshore_bad_kmh"]:
        return 0.55, "onshore"
    return 0.25, "onshore fort"


@dataclass
class HourScore:
    time: str
    score: float
    wave_height: float
    wave_period: float
    wave_direction: float
    wind_speed: float
    wind_direction: float
    wind_gusts: float | None
    wind_label: str
    period_label: str


def score_hour(hour: dict, spot: dict, criteria: dict) -> HourScore:
    h = hour["wave_height"] or 0.0
    p = hour["wave_period"] or 0.0
    wd = hour["wave_direction"] if hour["wave_direction"] is not None else spot["best_swell_dir"]
    ws = hour["wind_speed"] or 0.0
    wdir = hour["wind_direction"] if hour["wind_direction"] is not None else 0.0

    pf, plabel = period_factor(p, criteria)
    wf, wlabel = wind_factor(ws, wdir, spot, criteria)
    score = height_score(h, spot) * pf * direction_factor(wd, spot) * wf
    return HourScore(
        time=hour["time"], score=round(min(score, 10.0), 1),
        wave_height=h, wave_period=p, wave_direction=wd,
        wind_speed=ws, wind_direction=wdir, wind_gusts=hour.get("wind_gusts"),
        wind_label=wlabel, period_label=plabel,
    )


def verdict(score: float, criteria: dict) -> tuple[str, str]:
    for v in criteria["verdicts"]:
        if score >= v["min"]:
            return v["emoji"], v["label"]
    last = criteria["verdicts"][-1]
    return last["emoji"], last["label"]


def best_window(scores: list[HourScore], threshold: float = 4.0) -> tuple[str, str] | None:
    """Plus longue plage horaire consécutive >= threshold autour du meilleur score."""
    if not scores:
        return None
    best_i = max(range(len(scores)), key=lambda i: scores[i].score)
    if scores[best_i].score < threshold:
        return None
    lo = hi = best_i
    while lo > 0 and scores[lo - 1].score >= threshold:
        lo -= 1
    while hi < len(scores) - 1 and scores[hi + 1].score >= threshold:
        hi += 1
    return scores[lo].time[11:16], scores[hi].time[11:16]
