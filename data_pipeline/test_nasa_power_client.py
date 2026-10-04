from nasa_power_client import _parse_power_response, NasaPowerError


def _sample_response(overrides=None):
    """Builds a response matching NASA POWER's documented JSON shape."""
    data = {
        "properties": {
            "parameter": {
                "T2M": {"20240501": 32.1, "20240502": 33.4, "20240503": -999},
                "RH2M": {"20240501": 68.2, "20240502": 61.0, "20240503": 55.0},
                "WS2M": {"20240501": 2.3, "20240502": 1.9, "20240503": 2.0},
                "ALLSKY_SFC_SW_DWN": {"20240501": 19.1, "20240502": 20.4, "20240503": 18.0},
            }
        }
    }
    if overrides:
        data["properties"]["parameter"].update(overrides)
    return data


def test_parses_valid_days():
    rows = _parse_power_response(_sample_response())
    # Day 3 has a -999 (missing) temperature and should be dropped entirely.
    assert len(rows) == 2
    assert rows[0]["date"] == "20240501"
    assert rows[0]["temperature_c"] == 32.1
    assert rows[0]["relative_humidity_pct"] == 68.2
    assert rows[0]["wind_speed_ms"] == 2.3
    assert rows[0]["solar_radiation_kwh_m2"] == 19.1


def test_rows_are_sorted_by_date():
    rows = _parse_power_response(_sample_response())
    dates = [r["date"] for r in rows]
    assert dates == sorted(dates)


def test_missing_parameter_raises():
    data = _sample_response()
    del data["properties"]["parameter"]["WS2M"]
    try:
        _parse_power_response(data)
        assert False, "expected NasaPowerError"
    except NasaPowerError:
        pass


def test_malformed_response_raises():
    try:
        _parse_power_response({"unexpected": "shape"})
        assert False, "expected NasaPowerError"
    except NasaPowerError:
        pass


if __name__ == "__main__":
    import sys
    current_module = sys.modules[__name__]
    passed, failed = 0, 0
    for name in dir(current_module):
        if name.startswith("test_"):
            fn = getattr(current_module, name)
            try:
                fn()
                print(f"PASS  {name}")
                passed += 1
            except AssertionError as e:
                print(f"FAIL  {name}: {e}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
