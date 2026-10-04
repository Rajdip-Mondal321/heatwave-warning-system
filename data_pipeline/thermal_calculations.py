"""
Thermal stress index formulas: simplified outdoor WBGT and NOAA Heat Index.

These are the same formulas used in the personalized risk engine, so a
WBGT value computed here from NASA POWER historical data is directly
comparable to a WBGT value computed live from a weather API.
"""

import math


def water_vapor_pressure_hpa(temp_c: float, rh_percent: float) -> float:
    """Water vapor pressure (hPa) from temperature (C) and relative humidity (%)."""
    return (rh_percent / 100.0) * 6.105 * math.exp(17.27 * temp_c / (237.7 + temp_c))


def calculate_wbgt(temp_c: float, rh_percent: float) -> float:
    """
    Simplified outdoor WBGT approximation (Australian Bureau of Meteorology
    formula) -- doesn't require a physical globe-thermometer/radiation sensor.
    """
    e = water_vapor_pressure_hpa(temp_c, rh_percent)
    return 0.567 * temp_c + 0.393 * e + 3.94


def calculate_heat_index_c(temp_c: float, rh_percent: float) -> float:
    """
    NOAA/NWS Heat Index (Rothfusz regression). Valid above ~27C / 40% RH;
    below that the "feels like" temperature is close to the actual
    temperature, so we just return temp_c unchanged in that range.
    """
    if temp_c < 26.7 or rh_percent < 40:
        return temp_c

    t_f = temp_c * 9 / 5 + 32
    r = rh_percent

    hi_f = (
        -42.379
        + 2.04901523 * t_f
        + 10.14333127 * r
        - 0.22475541 * t_f * r
        - 0.00683783 * t_f ** 2
        - 0.05481717 * r ** 2
        + 0.00122874 * t_f ** 2 * r
        + 0.00085282 * t_f * r ** 2
        - 0.00000199 * t_f ** 2 * r ** 2
    )
    return (hi_f - 32) * 5 / 9


def wbgt_risk_band(wbgt_c: float) -> str:
    """Standard WBGT-based risk bands, in Celsius."""
    if wbgt_c < 27:
        return "Low"
    if wbgt_c < 29:
        return "Moderate"
    if wbgt_c < 31:
        return "High"
    if wbgt_c < 33:
        return "Severe"
    return "Extreme"
