"""Weather service behaviour tests."""

import pytest

from django.core.cache import cache
from django.test.utils import override_settings

from apps.weather.schemas import Forecast, OWMPeriod
from apps.weather.services import WeatherService


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
@pytest.mark.asyncio
async def test_service_caches_primary_provider(monkeypatch):
    cache.clear()

    service = WeatherService(cache_timeout=60)

    sample_forecast = Forecast(
        location_name="Taipei",
        country="TW",
        units="metric",
        source="owm",
        periods=[
            OWMPeriod(
                ts="2025-09-22T00:00:00+00:00",
                temp=24.5,
                desc="clear",
            )
        ],
    )

    call_count = {"owm": 0}

    async def fake_owm_fetch(**kwargs):
        call_count["owm"] += 1
        return sample_forecast

    monkeypatch.setattr(service._adapters["owm"], "fetch_forecast", fake_owm_fetch)

    result_one = await service.get_forecast(city="Taipei", country="TW")
    result_two = await service.get_forecast(city="Taipei", country="TW")

    assert result_one.source == "owm"
    assert result_two.source == "owm"
    assert call_count["owm"] == 1


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
@pytest.mark.asyncio
async def test_service_fallbacks_to_secondary_provider(monkeypatch):
    cache.clear()

    service = WeatherService(cache_timeout=0)

    async def failing_cwa_fetch(**kwargs):  # pragma: no cover - simulated failure
        raise RuntimeError("CWA unavailable")

    fallback_forecast = Forecast(
        location_name="Taipei",
        country="TW",
        units="metric",
        source="owm",
        periods=[
            OWMPeriod(
                ts="2025-09-22T03:00:00+00:00",
                temp=25.0,
                desc="scattered clouds",
            )
        ],
    )

    async def fallback_owm_fetch(**kwargs):
        return fallback_forecast

    monkeypatch.setattr(service._adapters["cwa"], "fetch_forecast", failing_cwa_fetch)
    monkeypatch.setattr(service._adapters["owm"], "fetch_forecast", fallback_owm_fetch)

    result = await service.get_forecast(
        provider="cwa",
        location_name="Taipei",
        city="Taipei",
        country="TW",
    )

    assert result.source == "owm"
    assert result.periods[0].temp == 25.0
