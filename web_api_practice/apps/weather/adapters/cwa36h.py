"""Adapter for Taiwan CWA 36-hour forecast dataset."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx
from django.conf import settings

from .base import BaseWeatherAdapter
from ...common.http import get as http_get
from ...common.utils import to_iso_utc
from ..schemas import Forecast, Period


class Cwa36hAdapter(BaseWeatherAdapter):
    """Fetch and normalize Central Weather Administration 36h forecasts."""

    BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

    async def fetch_forecast(
        self,
        *,
        location_name: str,
        country: str = "TW",
        units: str = "metric",
    ) -> Forecast:
        params = {
            "Authorization": getattr(settings, "CWA_API_KEY", settings.ENV.get("CWA_API_KEY", "")),
            "locationName": location_name,
        }

        async with httpx.AsyncClient(timeout=settings.HTTP_DEFAULT_TIMEOUT) as client:
            response = await http_get(client, self.BASE_URL, params=params)
            payload: Dict[str, Any] = response.json()

        records = payload.get("records") or {}
        locations = records.get("location") or []
        if not locations:
            return Forecast(
                location_name=location_name,
                country=country,
                units=units,
                source="cwa",
                periods=[],
            )

        location = locations[0]
        actual_name = location.get("locationName") or location_name
        elements: Dict[str, List[Dict[str, Any]]] = {
            element.get("elementName"): element.get("time") or []
            for element in location.get("weatherElement", [])
        }

        wx_times = elements.get("Wx", [])
        temp_times = elements.get("T", [])
        humidity_times = elements.get("RH", [])
        wind_times = elements.get("WS", [])

        periods: List[Period] = []
        for idx, wx_entry in enumerate(wx_times):
            temp_entry = temp_times[idx] if idx < len(temp_times) else None
            humidity_entry = humidity_times[idx] if idx < len(humidity_times) else None
            wind_entry = wind_times[idx] if idx < len(wind_times) else None

            period = self._build_period(wx_entry, temp_entry, humidity_entry, wind_entry)
            if period:
                periods.append(period)

        return Forecast(
            location_name=actual_name,
            country=country,
            units=units,
            source="cwa",
            periods=periods,
        )

    @staticmethod
    def _build_period(
        wx_entry: Dict[str, Any],
        temp_entry: Dict[str, Any] | None,
        humidity_entry: Dict[str, Any] | None,
        wind_entry: Dict[str, Any] | None,
    ) -> Period | None:
        description = (wx_entry.get("parameter") or {}).get("parameterName")
        if not description:
            return None

        temp_value = None
        if temp_entry:
            temp_value = (temp_entry.get("parameter") or {}).get("parameterName")

        if temp_value is None:
            return None

        humidity_value = None
        if humidity_entry:
            humidity_value = (humidity_entry.get("parameter") or {}).get("parameterName")

        wind_value = None
        if wind_entry:
            wind_value = (wind_entry.get("parameter") or {}).get("parameterName")

        start_time = (
            wx_entry.get("startTime")
            or wx_entry.get("dataTime")
            or (temp_entry or {}).get("startTime")
            or ""
        )

        try:
            temp_float = float(temp_value)
        except (TypeError, ValueError):
            return None

        humidity_int = None
        try:
            if humidity_value is not None:
                humidity_int = int(float(humidity_value))
        except (TypeError, ValueError):
            humidity_int = None

        wind_kph = None
        try:
            if wind_value is not None:
                wind_kph = float(wind_value) * 3.6
        except (TypeError, ValueError):
            wind_kph = None

        return Period(
            ts=to_iso_utc(start_time),
            temp=temp_float,
            desc=description,
            humidity=humidity_int,
            wind_kph=wind_kph,
        )

