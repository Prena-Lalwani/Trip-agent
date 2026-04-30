import requests
from langchain_core.tools import tool

from app.core.config import settings


@tool
def get_current_weather(city: str) -> str:
    """Get current weather conditions for a city."""
    try:
        resp = requests.get(
            "http://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": settings.openweather_api_key, "units": "metric"},
            timeout=10,
        )
        resp.raise_for_status()
        d = resp.json()
        return (
            f"Current weather in {city}: {d['weather'][0]['description'].capitalize()}, "
            f"Temp: {d['main']['temp']}°C (feels like {d['main']['feels_like']}°C), "
            f"Humidity: {d['main']['humidity']}%, Wind: {d['wind']['speed']} m/s"
        )
    except Exception as e:
        return f"Could not fetch current weather for {city}: {e}"


@tool
def get_weather_forecast(city: str) -> str:
    """Get a 5-day weather forecast for a city (one reading per day)."""
    try:
        resp = requests.get(
            "http://api.openweathermap.org/data/2.5/forecast",
            params={"q": city, "appid": settings.openweather_api_key, "units": "metric", "cnt": 5},
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("list", [])
        lines = [
            f"- {item['dt_txt']}: {item['weather'][0]['description']}, {item['main']['temp']}°C"
            for item in items
        ]
        return f"Forecast for {city}:\n" + "\n".join(lines)
    except Exception as e:
        return f"Could not fetch forecast for {city}: {e}"
