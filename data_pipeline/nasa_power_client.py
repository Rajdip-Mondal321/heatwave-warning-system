"""
Client for NASA POWER's historical daily point API.

Free, no API key required. One request returns the full date range for a
single lat/lon point, so fetching multiple years of history costs one
request per district -- not one request per day.

Docs: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
"""

import time
from datetime import date
from typing import List, Dict, Any, Optional

import requests

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# NASA POWER uses -999 (occasionally -999.0) as a "no data" sentinel.
MISSING_VALUE = -999

PARAMETERS = ["T2M", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN"]
# T2M                : temperature at 2m, deg C
# RH2M               : relative humidity at 2m, %
# WS2M               : wind speed at 2m, m/s
# ALLSKY_SFC_SW_DWN  : all-sky surface shortwave downward irradiance, kWh/m^2/day


class NasaPowerError(RuntimeError):
    """Raised when NASA POWER returns an unexpected response shape."""


def fetch_historical_weather(
    latitude: float,
    longitude: float,
    start: date,
    end: date,
    max_retries: int = 3,
    timeout: int = 60,
) -> List[Dict[str, Any]]:
    """
    Fetch daily T2M / RH2M / WS2M / solar radiation for one point across a
    date range. Returns a list of per-day dicts, oldest first, with missing
    days/values (NASA POWER's -999 sentinel) excluded rather than passed
    through as garbage.
    """
    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "RE",
        "longitude": longitude,
        "latitude": latitude,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }

    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(POWER_URL, params=params, timeout=timeout)
            response.raise_for_status()
            return _parse_power_response(response.json())
        except (requests.RequestException, NasaPowerError) as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # 2s, 4s, 8s backoff
    raise NasaPowerError(
        f"Failed to fetch NASA POWER data for ({latitude}, {longitude}) "
        f"after {max_retries} attempts: {last_error}"
    )


def _parse_power_response(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        param_block = data["properties"]["parameter"]
    except KeyError as exc:
        raise NasaPowerError(f"Unexpected response shape, missing key: {exc}")

    missing_params = [p for p in PARAMETERS if p not in param_block]
    if missing_params:
        raise NasaPowerError(f"Response missing expected parameters: {missing_params}")

    # All parameters share the same set of date keys (YYYYMMDD strings).
    dates = sorted(param_block[PARAMETERS[0]].keys())

    rows = []
    for date_str in dates:
        raw = {p: param_block[p].get(date_str) for p in PARAMETERS}

        if any(v is None or float(v) <= MISSING_VALUE for v in raw.values()):
            continue  # skip days with any missing sentinel value

        rows.append({
            "date": date_str,  # YYYYMMDD
            "temperature_c": float(raw["T2M"]),
            "relative_humidity_pct": float(raw["RH2M"]),
            "wind_speed_ms": float(raw["WS2M"]),
            "solar_radiation_kwh_m2": float(raw["ALLSKY_SFC_SW_DWN"]),
        })

    return rows


if __name__ == "__main__":
    # Smoke test -- run this file directly to confirm connectivity and
    # response parsing before running the full district loop. This could
    # not be exercised from the sandbox that generated this file (no
    # network access there), so please run it yourself as a first check.
    sample = fetch_historical_weather(
        latitude=22.5726,
        longitude=88.3639,
        start=date(2024, 5, 1),
        end=date(2024, 5, 7),
    )
    for row in sample:
        print(row)
