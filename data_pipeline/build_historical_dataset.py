"""
Builds a historical WBGT/Heat Index training dataset from NASA POWER, for
every district in districts.py, ready to feed into an XGBoost training
script as-is.

Usage:
    python build_historical_dataset.py --start 2019-01-01 --end 2024-12-31

Output columns:
    district, state, latitude, longitude, date, month, day_of_year,
    temperature_c, relative_humidity_pct, wind_speed_ms,
    solar_radiation_kwh_m2, wbgt_c, heat_index_c, wbgt_risk_band,
    wbgt_lag1, wbgt_roll3, wbgt_next_day   <- regression target

Safe to re-run: districts already present in the output CSV are skipped,
so an interrupted run (network hiccup, rate limit, etc.) can just be
restarted with the same command.

Note on scope: this builds a dataset of *historical actuals*. True
forecast bias-correction (training XGBoost to correct Open-Meteo's
forecast against what actually happened) needs forecast-vs-actual pairs,
which can't be reconstructed retroactively -- Open-Meteo doesn't archive
past forecasts. If you want that, the next step is a small script that
logs today's live forecast daily going forward, so those pairs start
accumulating. Ask if you want that scaffolded too.
"""

import argparse
import csv
import os
import time
from datetime import date, datetime
from typing import Set

from districts import DISTRICTS
from nasa_power_client import fetch_historical_weather, NasaPowerError
from thermal_calculations import calculate_wbgt, calculate_heat_index_c, wbgt_risk_band

OUTPUT_COLUMNS = [
    "district", "state", "latitude", "longitude", "date", "month", "day_of_year",
    "temperature_c", "relative_humidity_pct", "wind_speed_ms", "solar_radiation_kwh_m2",
    "wbgt_c", "heat_index_c", "wbgt_risk_band",
    "wbgt_lag1", "wbgt_roll3", "wbgt_next_day",
]

REQUEST_DELAY_SECONDS = 1.0  # be polite to the free API when looping over many districts


def _already_fetched_districts(output_path: str) -> Set[str]:
    """Districts that already have rows in the output CSV, so re-runs can skip them."""
    if not os.path.exists(output_path):
        return set()
    done = set()
    with open(output_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            done.add(row["district"])
    return done


def _engineer_features(rows: list) -> list:
    """Adds lag / rolling-average / next-day-target columns to a district's
    chronologically sorted rows. Assumes rows are already sorted by date."""
    enriched = []
    wbgt_history = []

    for i, row in enumerate(rows):
        wbgt_history.append(row["wbgt_c"])

        row["wbgt_lag1"] = wbgt_history[i - 1] if i >= 1 else ""
        row["wbgt_roll3"] = (
            round(sum(wbgt_history[max(0, i - 2):i + 1]) / len(wbgt_history[max(0, i - 2):i + 1]), 2)
        )
        # Target: tomorrow's WBGT. Last row in the series has no "tomorrow"
        # yet, so it's left blank and should be dropped before training.
        enriched.append(row)

    for i in range(len(enriched) - 1):
        enriched[i]["wbgt_next_day"] = enriched[i + 1]["wbgt_c"]
    if enriched:
        enriched[-1]["wbgt_next_day"] = ""

    return enriched


def build_dataset(start: date, end: date, output_path: str) -> None:
    already_done = _already_fetched_districts(output_path)
    if already_done:
        print(f"Resuming: {len(already_done)} district(s) already in {output_path}, will skip those.")

    file_exists = os.path.exists(output_path)
    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        if not file_exists:
            writer.writeheader()

        for i, loc in enumerate(DISTRICTS, start=1):
            if loc["district"] in already_done:
                continue

            print(f"[{i}/{len(DISTRICTS)}] Fetching {loc['district']}, {loc['state']} ...")
            try:
                daily = fetch_historical_weather(
                    latitude=loc["latitude"],
                    longitude=loc["longitude"],
                    start=start,
                    end=end,
                )
            except NasaPowerError as exc:
                print(f"  SKIPPED ({loc['district']}): {exc}")
                continue

            rows = []
            for day in daily:
                d = datetime.strptime(day["date"], "%Y%m%d").date()
                wbgt = round(calculate_wbgt(day["temperature_c"], day["relative_humidity_pct"]), 2)
                hi = round(calculate_heat_index_c(day["temperature_c"], day["relative_humidity_pct"]), 2)

                rows.append({
                    "district": loc["district"],
                    "state": loc["state"],
                    "latitude": loc["latitude"],
                    "longitude": loc["longitude"],
                    "date": d.isoformat(),
                    "month": d.month,
                    "day_of_year": d.timetuple().tm_yday,
                    "temperature_c": day["temperature_c"],
                    "relative_humidity_pct": day["relative_humidity_pct"],
                    "wind_speed_ms": day["wind_speed_ms"],
                    "solar_radiation_kwh_m2": day["solar_radiation_kwh_m2"],
                    "wbgt_c": wbgt,
                    "heat_index_c": hi,
                    "wbgt_risk_band": wbgt_risk_band(wbgt),
                })

            rows = _engineer_features(rows)
            writer.writerows(rows)
            f.flush()
            print(f"  wrote {len(rows)} day(s)")

            time.sleep(REQUEST_DELAY_SECONDS)

    print(f"\nDone. Dataset written to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--output", default="historical_wbgt_dataset.csv")
    args = parser.parse_args()

    build_dataset(
        start=datetime.strptime(args.start, "%Y-%m-%d").date(),
        end=datetime.strptime(args.end, "%Y-%m-%d").date(),
        output_path=args.output,
    )
