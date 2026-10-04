
import requests

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_current_weather(latitude: float, longitude: float) -> dict:
    """
    Fetch current weather data for a given location.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "wind_speed_10m"
        ),
        "timezone": "auto"
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    return {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": data.get("timezone"),
        "current": data.get("current")
    }


if __name__ == "__main__":
    weather = fetch_current_weather(
        latitude=26.1445,
        longitude=91.7362
    )

    print(weather)


def fetch_weather_for_locations(locations: list[dict]) -> list[dict]:
    """Fetch current weather for multiple locations in one request."""

    if not locations:
        return []

    latitudes = ",".join(
        str(item["latitude"]) for item in locations
    )

    longitudes = ",".join(
        str(item["longitude"]) for item in locations
    )

    params = {
        "latitude": latitudes,
        "longitude": longitudes,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "wind_speed_10m"
        ),
        "timezone": "auto"
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    # Multiple coordinates return a list of weather responses.
    if isinstance(data, dict):
        data = [data]

    results = []

    for location, weather in zip(locations, data):
        results.append({
            **location,
            "timezone": weather.get("timezone"),
            "current": weather.get("current")
        })

    return results