"""Adapter for The Movie Database (TMDb) search API."""

from __future__ import annotations

from typing import Any

import httpx
from django.conf import settings

from ...common.http import get as http_get
from ..schemas import Movie, SearchResult
from .base import BaseMoviesAdapter


class TmdbAdapter(BaseMoviesAdapter):
    """Fetch movie search results from TMDb and normalize them."""

    BASE_URL = "https://api.themoviedb.org/3/search/movie"

    async def search(self, *, query: str, page: int = 1, lang: str = "zh-TW") -> SearchResult:
        api_key = getattr(settings, "TMDB_API_KEY", None)

        if not api_key:
            raise RuntimeError("TMDB_API_KEY is not configured")

        params: dict[str, Any] = {
            "api_key": api_key,
            "query": query,
            "page": page,
            "language": lang,
        }

        timeout = getattr(settings, "HTTP_DEFAULT_TIMEOUT", 8.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await http_get(client, self.BASE_URL, params=params)
        payload = response.json()

        image_base = getattr(settings, "TMDB_IMAGE_BASE", "https://image.tmdb.org/t/p/w500")
        items: list[Movie] = []
        for raw in payload.get("results", []) or []:
            poster_path = raw.get("poster_path")
            poster_url = f"{image_base}{poster_path}" if poster_path else None

            items.append(
                Movie(
                    id=str(raw.get("id", "")),
                    title=raw.get("title", ""),
                    year=(raw.get("release_date", "")[:4] or None),
                    plot=raw.get("overview"),
                    poster=poster_url,
                    genres=raw.get("genre_ids"),
                    rating=raw.get("vote_average"),
                    source="tmdb",
                )
            )

        return SearchResult(
            items=items,
            page=int(payload.get("page", 1) or 1),
            total_pages=int(payload.get("total_pages", 1) or 1),
            total_results=int(payload.get("total_results", len(items)) or len(items)),
            source="tmdb",
        )
