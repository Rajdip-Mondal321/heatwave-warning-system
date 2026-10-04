
from fastapi import FastAPI, HTTPException

from weather_pipeline import fetch_weather_for_locations


app = FastAPI(
    title="Heatwave Warning System API"
)


# Starter dataset for testing.
# Replace this with your complete Indian district dataset.
DISTRICTS = [
    {
        "district": "Kolkata",
        "state": "West Bengal",
        "latitude": 22.5726,
        "longitude": 88.3639
    },
    {
        "district": "Siliguri",
        "state": "West Bengal",
        "latitude": 26.7271,
        "longitude": 88.3953
    },
    {
        "district": "New Delhi",
        "state": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090
    },
    {
        "district": "Mumbai City",
        "state": "Maharashtra",
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    {
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "latitude": 12.9716,
        "longitude": 77.5946
    },
    {
        "district": "Chennai",
        "state": "Tamil Nadu",
        "latitude": 13.0827,
        "longitude": 80.2707
    },
    {
        "district": "Hyderabad",
        "state": "Telangana",
        "latitude": 17.3850,
        "longitude": 78.4867
    },
    {
        "district": "Ahmedabad",
        "state": "Gujarat",
        "latitude": 23.0225,
        "longitude": 72.5714
    },
    {
        "district": "Jaipur",
        "state": "Rajasthan",
        "latitude": 26.9124,
        "longitude": 75.7873
    },
    {
        "district": "Lucknow",
        "state": "Uttar Pradesh",
        "latitude": 26.8467,
        "longitude": 80.9462
    },
    {
        "district": "Patna",
        "state": "Bihar",
        "latitude": 25.5941,
        "longitude": 85.1376
    },
    {
        "district": "Bhopal",
        "state": "Madhya Pradesh",
        "latitude": 23.2599,
        "longitude": 77.4126
    }
]


@app.get("/")
def home():
    return {
        "message": "Heatwave Warning System API is running"
    }


@app.get("/authority/district-weather")
def district_weather():

    try:
        weather = fetch_weather_for_locations(DISTRICTS)

        return {
            "coverage": "Starter monitoring locations",
            "count": len(weather),
            "districts": weather
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Weather provider error: {exc}"
        )