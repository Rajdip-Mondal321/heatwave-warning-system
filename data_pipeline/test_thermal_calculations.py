from thermal_calculations import calculate_wbgt, calculate_heat_index_c, wbgt_risk_band


def test_wbgt_hot_humid_day():
    # 38C / 70% RH -- a typical severe pre-monsoon heatwave day in eastern India.
    # This simplified BOM approximation can legitimately exceed air temperature
    # at high humidity (the vapor-pressure term dominates), so the upper bound
    # here is wide on purpose -- it's a known property of the formula, not a bug.
    wbgt = calculate_wbgt(38, 70)
    assert 33 < wbgt < 48, f"expected a high WBGT, got {wbgt}"
    assert wbgt_risk_band(wbgt) == "Extreme"


def test_wbgt_mild_day():
    # 22C / 50% RH -- comfortable conditions
    wbgt = calculate_wbgt(22, 50)
    assert wbgt < 22, f"expected WBGT below air temp in mild/dry conditions, got {wbgt}"
    assert wbgt_risk_band(wbgt) == "Low"


def test_heat_index_matches_known_range():
    # 35C / 50% RH -- NWS-style reference point, expected apparent temp ~40-43C
    hi = calculate_heat_index_c(35, 50)
    assert 39 <= hi <= 45, f"expected ~40-43C, got {hi}"


def test_heat_index_below_threshold_returns_actual_temp():
    hi = calculate_heat_index_c(20, 30)
    assert hi == 20


def test_wbgt_risk_bands_are_monotonic():
    bands = [wbgt_risk_band(t) for t in [20, 27, 29, 31, 33, 36]]
    assert bands == ["Low", "Moderate", "High", "Severe", "Extreme", "Extreme"]


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
