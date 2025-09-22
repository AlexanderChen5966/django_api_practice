"""Adapter for the OpenWeatherMap 5-day/3-hour forecast API."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx
from django.conf import settings

from .base import BaseWeatherAdapter
from ...common.http import get as http_get
from ...common.utils import to_iso_utc
from ..schemas import Forecast, OWMPeriod


class OpenWeatherAdapter(BaseWeatherAdapter):
    """Fetch and normalize forecast data from OpenWeatherMap."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

    async def fetch_forecast(
        self,
        *,
        city: str,
        country: str,
        lang: str = "zh_tw",
        units: str = "metric",
    ) -> Forecast:
        params = {
            "q": f"{city},{country}",
            "APPID": getattr(settings, "OWM_API_KEY", settings.ENV.get("OWM_API_KEY", "")),
            "lang": lang,
            "units": units,
        }

        async with httpx.AsyncClient(timeout=settings.HTTP_DEFAULT_TIMEOUT) as client:
            response = await http_get(client, self.BASE_URL, params=params)
            payload: Dict[str, Any] = response.json()

        city_info: Dict[str, Any] = payload.get("city") or {}
        location_name = city_info.get("name") or city
        country_code = city_info.get("country") or country

        periods: List[OWMPeriod] = []
        for entry in payload.get("list", []):
            period = self._build_period(entry)
            if period:
                periods.append(period)

        return Forecast(
            location_name=location_name,
            country=country_code,
            units=units,
            source="owm",
            periods=periods,
        )

    @staticmethod
    def _build_period(entry: Dict[str, Any]) -> OWMPeriod | None:
        main = entry.get("main") or {}
        weather_items = entry.get("weather") or []
        wind = entry.get("wind") or {}

        temp = main.get("temp")
        if temp is None or not weather_items:
            return None

        description = weather_items[0].get("description") or ""
        humidity = main.get("humidity")
        speed = wind.get("speed")

        ts_raw = entry.get("dt_txt") or ""
        ts_iso = to_iso_utc(ts_raw)

        wind_kph = float(speed) * 3.6 if isinstance(speed, (int, float)) else None

        return OWMPeriod(
            ts=ts_iso,
            temp=float(temp),
            desc=description,
            humidity=int(humidity) if isinstance(humidity, (int, float)) else None,
            wind_kph=wind_kph,
        )
