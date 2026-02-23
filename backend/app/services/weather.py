"""Weather service using Open-Meteo API."""
import httpx
from datetime import datetime
from typing import Dict, Any


class WeatherService:
    """Service for fetching weather data from Open-Meteo."""

    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    async def get_historical_weather(
        self,
        lat: float,
        lon: float,
        dt: datetime,
    ) -> Dict[str, Any]:
        """Fetch historical weather for a specific location and time."""
        date_str = dt.date().isoformat()
        hour = dt.hour

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "auto",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        hourly = data.get("hourly", {})

        # Get data for the specific hour
        temp = self._get_hourly_value(hourly, "temperature_2m", hour)
        feels_like = self._get_hourly_value(hourly, "apparent_temperature", hour)
        humidity = self._get_hourly_value(hourly, "relative_humidity_2m", hour)
        wind_speed = self._get_hourly_value(hourly, "wind_speed_10m", hour)
        wind_dir = self._get_hourly_value(hourly, "wind_direction_10m", hour)
        precip = self._get_hourly_value(hourly, "precipitation", hour)
        weather_code = self._get_hourly_value(hourly, "weather_code", hour)

        return {
            "temperature": temp,
            "feels_like": feels_like,
            "humidity": int(humidity) if humidity else None,
            "wind_speed": wind_speed,
            "wind_direction": self._degrees_to_direction(wind_dir) if wind_dir else None,
            "conditions": self._weather_code_to_condition(weather_code) if weather_code else None,
            "precipitation": precip,
        }

    def _get_hourly_value(self, hourly: Dict, key: str, hour: int):
        """Get a value from hourly data for a specific hour."""
        values = hourly.get(key, [])
        if hour < len(values):
            return values[hour]
        return None

    def _degrees_to_direction(self, degrees: float) -> str:
        """Convert wind direction degrees to compass direction."""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                      "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]

    def _weather_code_to_condition(self, code: int) -> str:
        """Convert WMO weather code to human-readable condition."""
        conditions = {
            0: "Clear",
            1: "Mainly Clear",
            2: "Partly Cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Foggy",
            51: "Light Drizzle",
            53: "Drizzle",
            55: "Heavy Drizzle",
            61: "Light Rain",
            63: "Rain",
            65: "Heavy Rain",
            66: "Freezing Rain",
            67: "Heavy Freezing Rain",
            71: "Light Snow",
            73: "Snow",
            75: "Heavy Snow",
            77: "Snow Grains",
            80: "Light Showers",
            81: "Showers",
            82: "Heavy Showers",
            85: "Light Snow Showers",
            86: "Heavy Snow Showers",
            95: "Thunderstorm",
            96: "Thunderstorm with Hail",
            99: "Heavy Thunderstorm",
        }
        return conditions.get(code, "Unknown")
