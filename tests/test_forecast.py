import unittest
from datetime import date

from surf_forecast import data, report, scoring, telegram

CONFIG = data.load_config()
CRIT = CONFIG["criteria"]
SPOT = CONFIG["spots"][0]


def fake_forecast(day: str, height, period, swell_dir, wind, wind_dir):
    times = [f"{day}T{h:02d}:00" for h in range(24)]
    n = len(times)
    marine = {"hourly": {
        "time": times, "wave_height": [height] * n, "wave_period": [period] * n,
        "wave_direction": [swell_dir] * n, "swell_wave_height": [height] * n,
        "swell_wave_period": [period] * n, "swell_wave_direction": [swell_dir] * n,
        "sea_surface_temperature": [15.5] * n,
    }}
    weather = {"hourly": {
        "time": times, "wind_speed_10m": [wind] * n,
        "wind_direction_10m": [wind_dir] * n, "wind_gusts_10m": [wind + 8] * n,
    }}
    return data.merge(marine, weather)


def hour(**kw):
    base = dict(time="2026-11-14T10:00", wave_height=1.2, wave_period=7,
                wave_direction=150, wind_speed=10, wind_direction=340, wind_gusts=15)
    base.update(kw)
    return base


class ScoringTest(unittest.TestCase):
    def test_ideal_conditions(self):
        s = scoring.score_hour(hour(), SPOT, CRIT)
        self.assertGreaterEqual(s.score, 8)
        self.assertEqual(scoring.verdict(s.score, CRIT)[0], "🔥")

    def test_flat(self):
        s = scoring.score_hour(hour(wave_height=0.2), SPOT, CRIT)
        self.assertEqual(s.score, 0)

    def test_strong_marin_kills_it(self):
        s = scoring.score_hour(hour(wind_speed=30, wind_direction=140), SPOT, CRIT)
        self.assertLess(s.score, 4)

    def test_short_period_penalised(self):
        good = scoring.score_hour(hour(), SPOT, CRIT).score
        chop = scoring.score_hour(hour(wave_period=3.5), SPOT, CRIT).score
        self.assertLess(chop, good / 2)

    def test_swell_out_of_window(self):
        s = scoring.score_hour(hour(wave_direction=300), SPOT, CRIT)
        self.assertLess(s.score, 3)

    def test_compass(self):
        self.assertEqual(scoring.compass(315), "NO")
        self.assertEqual(scoring.compass(135), "SE")
        self.assertEqual(scoring.compass(0), "N")


class ReportTest(unittest.TestCase):
    def test_report_contents(self):
        fc = fake_forecast("2026-11-14", 1.2, 7, 150, 10, 340)
        fc["hourly"] += fake_forecast("2026-11-15", 0.2, 3, 150, 25, 140)["hourly"]
        forecasts = {s["id"]: fc for s in CONFIG["spots"]}
        text = report.build_report(CONFIG, forecasts, date(2026, 11, 14))
        self.assertIn("AUJOURD'HUI", text)
        self.assertIn("IDÉAL", text)
        self.assertIn("Flat", text)
        self.assertIn("Créneau : 07:00 → 19:00", text)
        self.assertIn("3/2 mm", text)
        self.assertLess(len(text), 4096)

    def test_split(self):
        chunks = telegram.split_message("ligne\n" * 2000, limit=500)
        self.assertTrue(all(len(c) <= 500 for c in chunks))


if __name__ == "__main__":
    unittest.main()
