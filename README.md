# 🔥 Heat Stress Warning System

A web app that detects your location, shows real-time weather, and estimates your personal **heat stress risk** based on the weather, your age group, activity level, clothing and time spent outdoors. It also gives safety guidance and helps you find nearby hospitals when the risk is high.

## Features

- **Login and sign up** with username and password (accounts stored in the browser)
- **Forgot password** flow to reset a password
- **Automatic location detection** (latitude, longitude and city name)
- **Live weather data:** temperature, humidity, wind speed and apparent ("feels like") temperature
- **Check another city:** search any city and compare its weather
- **Personal heat risk calculator** using:
  - Age group (Adult, Child, Elderly)
  - Activity (Rest, Light, Moderate, Heavy)
  - Clothing (Light, Normal, Heavy)
  - Outdoor exposure hours
- **Risk levels:** Low, Moderate, High and Very High, with a percentage score
- **Safety guidance** that changes with the risk level
- **Nearby hospital finder** (opens Google Maps) when risk is 50% or higher
- **Dark glass-style UI** with an animated space background, responsive on mobile

## How the Risk Is Calculated

1. Apparent temperature is calculated from temperature, humidity and wind speed.
2. It is multiplied by factors for age, activity, clothing and exposure time.
3. The resulting score is converted into a risk percentage:

| Risk score | Base probability | Level |
|------------|------------------|-------|
| below 32   | 5%               | Low |
| 32 to 37   | 20%              | Moderate |
| 38 to 44   | 50%              | High |
| 45 and above | 80%            | Very High |

Extra points are added for more than 4 hours outdoors, elderly users and heavy activity (maximum 100%).

> ⚠️ This system is for general awareness only and is **not a medical diagnosis**.

## Tech Stack

- HTML, CSS and JavaScript (single-page frontend in `Templates/heat.html`)
- Python backend in the `backend/` folder
- [Open-Meteo API](https://open-meteo.com/): weather data and city search (no API key needed)
- [BigDataCloud](https://www.bigdatacloud.com/): reverse geocoding to get the city name
- Browser Geolocation API
- Google Maps: nearby hospital search

## Project Structure

```
heatwave-warning-system/
├── backend/
│   ├── main.py                # Backend entry point
│   └── weather_pipeline.py    # Weather data pipeline
├── data_pipeline/             # Data processing files
├── Templates/
│   └── heat.html              # Main web page (UI + logic)
├── .env.example               # Example environment variables
├── .gitignore
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Rajdip-Mondal321/heatwave-warning-system.git
cd heatwave-warning-system
```

### 2. Set up the backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Install dependencies and configure the environment:

```bash
pip install -r requirements.txt
cp .env.example .env
```

Then run the server:

```bash
python main.py
```

### 3. Open the app

Open the address shown in the terminal in your browser (for example `http://127.0.0.1:8000`).

You can also open `Templates/heat.html` directly in a browser. The page works on its own because it calls the weather APIs from the browser.

> 📍 Allow **location permission** in your browser when asked, otherwise your current weather cannot be detected.

## Usage

1. Create an account and sign in.
2. Allow location access to see your local weather.
3. (Optional) Search another city to compare weather.
4. Choose your age group, activity, clothing and outdoor hours.
5. Click **Calculate Heat Stress Risk** to see your risk level and safety tips.
6. If risk is high, click **Find Nearby Hospitals** to open Google Maps.

## Known Limitations

- Login accounts are stored in the browser's `localStorage`, and passwords are saved as plain text. This is a **demo login** only. Do not use real passwords. For real use, move authentication to the backend with hashed passwords.
- The risk formula is a simple estimate and has not been medically validated.
- Weather data accuracy depends on the Open-Meteo service.

## Future Improvements

- Secure server-side authentication with hashed passwords
- SMS or email heatwave alerts
- Multi-day heat forecast and charts
- Map view of high-risk areas
- Deployment to a cloud platform

## Author

**Rajdip Mondal**
GitHub: [@Rajdip-Mondal321](https://github.com/Rajdip-Mondal321)

## License

Add a license of your choice (for example MIT) in a `LICENSE` file.