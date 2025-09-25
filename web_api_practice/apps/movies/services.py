"""Movies domain service orchestrating providers, caching, and fallbacks."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from django.conf import settings
from django.core.cache import cache

from .adapters import BaseMoviesAdapter, OmdbAdapter, TmdbAdapter
from .schemas import SearchResult


class MoviesService:
    """Coordinate movie search providers with caching and graceful fallback."""

    DEFAULT_CACHE_TIMEOUT = 300
    DEFAULT_PRIMARY_PROVIDER = "tmdb"
    DEFAULT_PROVIDER_ORDER: tuple[str, ...] = ("tmdb", "omdb")
    DEFAULT_FALLBACKS: dict[str, tuple[str, ...]] = {
        "tmdb": ("omdb",),
        "omdb": ("tmdb",),
    }

    def __init__(
        self,
        *,
        cache_timeout: int | None = None,
        provider_order: Iterable[str] | None = None,
        fallbacks: Dict[str, Iterable[str]] | None = None,
    ) -> None:
        self._cache_timeout = cache_timeout or getattr(
            settings, "MOVIES_CACHE_TIMEOUT", self.DEFAULT_CACHE_TIMEOUT
        )

        configured_order = provider_order or getattr(
            settings, "MOVIES_PROVIDER_ORDER", self.DEFAULT_PROVIDER_ORDER
        )
        self._provider_order = tuple(name.lower() for name in configured_order)

        raw_fallbacks = fallbacks or getattr(
            settings, "MOVIES_PROVIDER_FALLBACKS", self.DEFAULT_FALLBACKS
        )
        self._fallbacks = {
            key.lower(): tuple(value)
            for key, value in raw_fallbacks.items()
        }

        self._adapters: dict[str, BaseMoviesAdapter] = {
            "tmdb": TmdbAdapter(),
            "omdb": OmdbAdapter(),
        }

    async def search(
        self,
        *,
        provider: str | None = None,
        **kwargs: Any,
    ) -> SearchResult:
        """Search movies using the requested provider and fallbacks when needed."""

        provider_chain = self._build_provider_chain(provider)
        last_error: Exception | None = None

        for provider_name in provider_chain:
            adapter = self._adapters.get(provider_name)
            if adapter is None:
                continue

            try:
                adapter_kwargs = self._normalize_kwargs(provider_name, kwargs)
            except ValueError as exc:
                last_error = exc
                continue

            cache_key = self._cache_key(provider_name, adapter_kwargs)
            cached = cache.get(cache_key)
            if isinstance(cached, SearchResult):
                return cached

            try:
                result = await adapter.search(**adapter_kwargs)
            except Exception as exc:  # noqa: BLE001 - fall back to next provider
                last_error = exc
                continue

            cache.set(cache_key, result, timeout=self._cache_timeout)
            return result

        if last_error:
            raise last_error
        raise RuntimeError("No movie provider available for the given parameters")

    def _build_provider_chain(self, provider: str | None) -> tuple[str, ...]:
        if provider:
            primary = provider.lower()
            fallbacks = tuple(self._fallbacks.get(primary, ()))
            return (primary, *fallbacks)

        return self._provider_order

    @staticmethod
    def _normalize_kwargs(provider: str, original: Dict[str, Any]) -> Dict[str, Any]:
        provider_key = provider.lower()

        query = original.get("query")
        if not query:
            raise ValueError("Movie search requires a 'query' parameter")

        page = int(original.get("page", 1) or 1)

        if provider_key == "tmdb":
            lang = original.get("lang", "zh-TW")
            return {
                "query": query,
                "page": page,
                "lang": lang,
            }

        if provider_key == "omdb":
            return {
                "query": query,
                "page": page,
            }

        raise ValueError(f"Unsupported movie provider '{provider}'")

    @staticmethod
    def _cache_key(provider: str, params: Dict[str, Any]) -> str:
        serialized = ",".join(
            f"{key}={params[key]}"
            for key in sorted(params)
        )
        return f"movies:{provider}:{serialized}"

