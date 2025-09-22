"""Weather domain service orchestrating providers, caching, and fallbacks."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List

from django.conf import settings
from django.core.cache import cache

from .adapters import Cwa36hAdapter, OpenWeatherAdapter
from .adapters.base import BaseWeatherAdapter
from .schemas import Forecast


class WeatherService:
    """Fetch forecasts with caching, provider selection, and graceful fallback."""

    DEFAULT_CACHE_TIMEOUT = 300
    DEFAULT_PROVIDER_ORDER: tuple[str, ...] = ("cwa", "owm")
    DEFAULT_FALLBACKS: dict[str, tuple[str, ...]] = {
        "cwa": ("owm",),
        "owm": ("cwa",),
    }

    def __init__(
        self,
        *,
        cache_timeout: int | None = None,
        provider_order: Iterable[str] | None = None,
        fallbacks: Dict[str, Iterable[str]] | None = None,
    ) -> None:
        self._cache_timeout = cache_timeout or getattr(
            settings, "WEATHER_CACHE_TIMEOUT", self.DEFAULT_CACHE_TIMEOUT
        )

        self._provider_order = tuple(
            provider_order
            or getattr(settings, "WEATHER_PROVIDER_ORDER", self.DEFAULT_PROVIDER_ORDER)
        )

        raw_fallbacks = fallbacks or getattr(
            settings, "WEATHER_PROVIDER_FALLBACKS", self.DEFAULT_FALLBACKS
        )
        self._fallbacks = {
            key: tuple(value)
            for key, value in raw_fallbacks.items()
        }

        self._adapters: dict[str, BaseWeatherAdapter] = {
            "owm": OpenWeatherAdapter(),
            "cwa": Cwa36hAdapter(),
        }

    async def get_forecast(
        self,
        *,
        provider: str | None = None,
        **kwargs: Any,
    ) -> Forecast:
        """Return a unified forecast, trying providers in order with caching."""

        provider_chain = self._build_provider_chain(provider)
        last_error: Exception | None = None

        for provider_name in provider_chain:
            adapter = self._adapters.get(provider_name)
            if adapter is None:
                continue

            try:
                normalized_kwargs = self._normalize_kwargs(provider_name, kwargs)
            except ValueError as exc:
                last_error = exc
                continue

            cache_key = self._cache_key(provider_name, normalized_kwargs)
            cached = cache.get(cache_key)
            if isinstance(cached, Forecast):
                return cached

            try:
                forecast = await adapter.fetch_forecast(**normalized_kwargs)
            except Exception as exc:  # noqa: BLE001 - surface provider error after fallbacks
                last_error = exc
                continue

            cache.set(cache_key, forecast, timeout=self._cache_timeout)
            return forecast

        if last_error:
            raise last_error
        raise RuntimeError("No provider available for the requested forecast")

    def _build_provider_chain(self, provider: str | None) -> List[str]:
        if provider:
            primary = provider.lower()
            fallbacks = list(self._fallbacks.get(primary, ()))
            return [primary, *fallbacks]

        return list(self._provider_order)

    def _normalize_kwargs(self, provider: str, original: Dict[str, Any]) -> Dict[str, Any]:
        provider = provider.lower()

        if provider == "owm":
            city = original.get("city")
            country = original.get("country")
            if not city or not country:
                raise ValueError("OpenWeatherMap requires 'city' and 'country' parameters")
            params: Dict[str, Any] = {
                "city": city,
                "country": country,
                "lang": original.get("lang", "zh_tw"),
                "units": original.get("units", "metric"),
            }
            return params

        if provider == "cwa":
            location_name = original.get("location_name") or original.get("locationName")
            if not location_name:
                raise ValueError("CWA adapter requires 'location_name' (or 'locationName') parameter")
            params = {
                "location_name": location_name,
                "country": original.get("country", "TW"),
                "units": original.get("units", "metric"),
            }
            return params

        raise ValueError(f"Unsupported provider '{provider}'")

    @staticmethod
    def _cache_key(provider: str, params: Dict[str, Any]) -> str:
        flatten = sorted(params.items())
        parts = [provider]
        for key, value in flatten:
            if is_dataclass(value):
                value_repr = asdict(value)
            elif isinstance(value, (dict, list, tuple)):
                value_repr = str(value)
            else:
                value_repr = value
            parts.append(f"{key}={value_repr}")
        return "|".join(parts)
