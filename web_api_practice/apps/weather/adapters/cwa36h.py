"""Adapter for Taiwan CWA 36-hour forecast dataset."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx
from django.conf import settings

from .base import BaseWeatherAdapter
from ...common.http import get as http_get
from ...common.utils import to_iso_utc
from ..schemas import Forecast, CWAPeriod


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

        wx_elements = elements.get("Wx", [])
        pop_elements = elements.get("PoP", [])
        minT_elements = elements.get("MinT", [])
        mxaT_elements = elements.get("MaxT", [])
        ci_elements = elements.get("CI", [])

        periods: List[CWAPeriod] = []
        for idx, wx_entry in enumerate(wx_elements):
            pop_entry = pop_elements[idx] if idx < len(pop_elements) else None
            minT_entry = minT_elements[idx] if idx < len(mxaT_elements) else None
            maxT_entry = mxaT_elements[idx] if idx < len(mxaT_elements) else None
            ci_entry = ci_elements[idx] if idx < len(ci_elements) else None

            period = self._build_period(wx_entry, pop_entry, minT_entry, maxT_entry,ci_entry)
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
        pop_entry: Dict[str, Any] | None,
        minT_entry: Dict[str, Any] | None,
        maxT_entry: Dict[str, Any] | None,
        ci_entry: Dict[str, Any] | None,

    ) -> CWAPeriod | None:
        description = (wx_entry.get("parameter") or {}).get("parameterName")
        if not description:
            return None

        pop_value = None
        if pop_entry:
            pop_value = (pop_entry.get("parameter") or {}).get("parameterName")

        if pop_value is None:
            return None

        minT_value = None
        if minT_entry:
            minT_value = (minT_entry.get("parameter") or {}).get("parameterName")

        maxT_value = None
        if maxT_entry:
            maxT_value = (maxT_entry.get("parameter") or {}).get("parameterName")

        ci_value = None
        if ci_entry:
            ci_value = (ci_entry.get("parameter") or {}).get("parameterName")

        start_time = (
            wx_entry.get("startTime")
            or wx_entry.get("dataTime")
            or (pop_entry or {}).get("startTime")
            or ""
        )

        # try:
        #     pop_str = float(pop_value)
        #
        # except (TypeError, ValueError):
        #     return None
        #
        # minT_int = None
        # try:
        #     if minT_value is not None:
        #         minT_int = int(minT_value)
        # except (TypeError, ValueError):
        #     minT_int = None
        #
        # wind_kph = None
        # try:
        #     if maxT_value is not None:
        #         maxT_int = int(float(maxT_value))
        # except (TypeError, ValueError):
        #     maxT_int = None
        #
        # try:
        #     if ci_value is not None:
        #         maxT_int = int(float(ci_value))
        # except (TypeError, ValueError):
        #     maxT_int = None

        return CWAPeriod(
            ts=to_iso_utc(start_time),
            desc=description,
            pop=pop_value,
            minT=minT_value,
            maxT=maxT_value,
            ci= ci_value
        )

