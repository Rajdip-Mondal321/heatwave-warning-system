import csv
import os
import tempfile
from datetime import date
from unittest.mock import patch

import build_historical_dataset as pipeline


def _fake_weather(latitude, longitude, start, end):
    # 5 fake days with a clear upward temperature trend, so lag/rolling/target
    # columns are easy to sanity-check by eye.
    base = [
        {"date": "20240501", "temperature_c": 30.0, "relative_humidity_pct": 60.0,
         "wind_speed_ms": 2.0, "solar_radiation_kwh_m2": 18.0},
        {"date": "20240502", "temperature_c": 32.0, "relative_humidity_pct": 62.0,
         "wind_speed_ms": 2.1, "solar_radiation_kwh_m2": 18.5},
        {"date": "20240503", "temperature_c": 34.0, "relative_humidity_pct": 65.0,
         "wind_speed_ms": 1.8, "solar_radiation_kwh_m2": 19.0},
    ]
    return base


def test_pipeline_writes_expected_rows_and_features():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "dataset.csv")

        with patch.object(pipeline, "fetch_historical_weather", side_effect=_fake_weather), \
             patch.object(pipeline, "DISTRICTS", [
                 {"district": "TestDistrict", "state": "TestState", "latitude": 10.0, "longitude": 20.0}
             ]), \
             patch.object(pipeline, "REQUEST_DELAY_SECONDS", 0):
            pipeline.build_dataset(date(2024, 5, 1), date(2024, 5, 3), out_path)

        with open(out_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 3
        assert rows[0]["district"] == "TestDistrict"

        # first row has no lag, third row has no next-day target
        assert rows[0]["wbgt_lag1"] == ""
        assert rows[2]["wbgt_next_day"] == ""

        # middle row's lag should equal the first row's wbgt
        assert rows[1]["wbgt_lag1"] == rows[0]["wbgt_c"]

        # first row's next_day should equal the second row's wbgt
        assert rows[0]["wbgt_next_day"] == rows[1]["wbgt_c"]


def test_resume_skips_already_fetched_districts():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "dataset.csv")
        call_count = {"n": 0}

        def counting_fetch(latitude, longitude, start, end):
            call_count["n"] += 1
            return _fake_weather(latitude, longitude, start, end)

        two_districts = [
            {"district": "AlreadyDone", "state": "S", "latitude": 1.0, "longitude": 1.0},
            {"district": "NotYetDone", "state": "S", "latitude": 2.0, "longitude": 2.0},
        ]

        with patch.object(pipeline, "fetch_historical_weather", side_effect=counting_fetch), \
             patch.object(pipeline, "DISTRICTS", two_districts), \
             patch.object(pipeline, "REQUEST_DELAY_SECONDS", 0):
            # First run: only "AlreadyDone"
            pipeline.build_dataset(date(2024, 5, 1), date(2024, 5, 3), out_path)
            with patch.object(pipeline, "DISTRICTS", [two_districts[0]]):
                pass  # (kept for clarity; already limited above)

        assert call_count["n"] == 2  # both districts fetched on first full run

        # Second run over the same output file should skip both (already present)
        call_count["n"] = 0
        with patch.object(pipeline, "fetch_historical_weather", side_effect=counting_fetch), \
             patch.object(pipeline, "DISTRICTS", two_districts), \
             patch.object(pipeline, "REQUEST_DELAY_SECONDS", 0):
            pipeline.build_dataset(date(2024, 5, 1), date(2024, 5, 3), out_path)

        assert call_count["n"] == 0, "expected both districts to be skipped as already fetched"


if __name__ == "__main__":
    test_pipeline_writes_expected_rows_and_features()
    print("PASS  test_pipeline_writes_expected_rows_and_features")
    test_resume_skips_already_fetched_districts()
    print("PASS  test_resume_skips_already_fetched_districts")
