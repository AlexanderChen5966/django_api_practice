"""Adapter for Taiwan CWA 36-hour forecast dataset."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

import httpx
from django.conf import settings

from .base import BaseWeatherAdapter
from ...common.http import get as http_get
from ...common.utils import to_iso_utc
from ..schemas import CWAPeriod, Forecast


class Cwa36hAdapter(BaseWeatherAdapter):
    """Fetch and normalize Central Weather Administration 36h forecasts."""

    BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    DEFAULT_ELEMENTS = ("Wx", "PoP", "MinT", "MaxT", "CI")

    async def fetch_forecast(
        self,
        *,
        location_name: str,
        country: str = "TW",
        units: str = "metric",
        elements: Iterable[str] | None = None,
    ) -> Forecast:
        params = {
            "Authorization": getattr(settings, "CWA_API_KEY", settings.ENV.get("CWA_API_KEY", "")),
            "locationName": location_name,
            "format": "JSON",
        }

        selected_elements = tuple(elements) if elements else self.DEFAULT_ELEMENTS
        if selected_elements:
            params["elementName"] = ",".join(selected_elements)

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
        elements_map: Dict[str, List[Dict[str, Any]]] = {
            entry.get("elementName"): entry.get("time") or []
            for entry in location.get("weatherElement", [])
        }

        wx_entries = elements_map.get("Wx", [])
        pop_entries = elements_map.get("PoP", [])
        min_entries = elements_map.get("MinT", [])
        max_entries = elements_map.get("MaxT", [])
        comfort_entries = elements_map.get("CI", [])

        periods: List[CWAPeriod] = []
        for idx, wx_entry in enumerate(wx_entries):
            period = self._build_period(
                wx_entry=wx_entry,
                pop_entry=_safe_get(pop_entries, idx),
                min_entry=_safe_get(min_entries, idx),
                max_entry=_safe_get(max_entries, idx),
                comfort_entry=_safe_get(comfort_entries, idx),
            )
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
        *,
        wx_entry: Dict[str, Any],
        pop_entry: Dict[str, Any] | None,
        min_entry: Dict[str, Any] | None,
        max_entry: Dict[str, Any] | None,
        comfort_entry: Dict[str, Any] | None,
    ) -> CWAPeriod | None:
        description = _get_parameter(wx_entry)
        if not description:
            return None

        pop_value = _parse_int(_get_parameter(pop_entry)) if pop_entry else None
        min_temp = _parse_float(_get_parameter(min_entry))
        max_temp = _parse_float(_get_parameter(max_entry))
        temps = [value for value in (min_temp, max_temp) if value is not None]
        avg_temp = sum(temps) / len(temps) if temps else None
        comfort = _get_parameter(comfort_entry)

        start_time = (
            wx_entry.get("startTime")
            or wx_entry.get("dataTime")
            or (min_entry or {}).get("startTime")
            or (max_entry or {}).get("startTime")
            or ""
        )
        end_time = wx_entry.get("endTime") or (min_entry or {}).get("endTime") or (max_entry or {}).get("endTime")

        return CWAPeriod(
            start=to_iso_utc(start_time),
            end=to_iso_utc(end_time) if end_time else None,
            desc=description,
            pop=pop_value,
            min_temp=min_temp,
            max_temp=max_temp,
            avg_temp=avg_temp,
            comfort=comfort,
        )


def _safe_get(items: List[Dict[str, Any]], index: int) -> Optional[Dict[str, Any]]:
    return items[index] if 0 <= index < len(items) else None


def _get_parameter(entry: Optional[Dict[str, Any]]) -> Optional[str]:
    if not entry:
        return None
    parameter = entry.get("parameter") or {}
    return parameter.get("parameterName")


def _parse_float(value: Optional[str]) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(float(value)) if value is not None else None
    except (TypeError, ValueError):
        return None

