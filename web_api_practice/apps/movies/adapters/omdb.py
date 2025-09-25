"""Adapter for the OMDb search API."""

from __future__ import annotations

import math
from typing import Any

import httpx
from django.conf import settings

from ...common.http import get as http_get
from ..schemas import Movie, SearchResult
from .base import BaseMoviesAdapter


class OmdbAdapter(BaseMoviesAdapter):
    """Fetch movie listings from OMDb and normalize them."""
    # omdb搜尋只能使用英文標題進行查詢
    BASE_URL = "https://www.omdbapi.com/"
    PAGE_SIZE = 10

    async def search(self, *, query: str, page: int = 1) -> SearchResult:
        api_key = getattr(settings, "OMDB_API_KEY", None)

        if not api_key:
            raise RuntimeError("OMDB_API_KEY is not configured")

        params: dict[str, Any] = {
            "apikey": api_key,
            "s": query,
            "type": "movie",
            "page": page,
        }

        timeout = getattr(settings, "HTTP_DEFAULT_TIMEOUT", 8.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await http_get(client, self.BASE_URL, params=params)
        payload = response.json()

        items: list[Movie] = []
        for raw in payload.get("Search", []) or []:
            poster = raw.get("Poster")
            poster_url = None if poster in (None, "N/A") else poster
            items.append(
                Movie(
                    id=raw.get("imdbID", ""),
                    title=raw.get("Title", ""),
                    year=raw.get("Year"),
                    poster=poster_url,
                    source="omdb",
                )
            )

        total_results = 0
        if payload.get("totalResults") not in (None, "N/A"):
            try:
                total_results = int(payload["totalResults"])
            except (TypeError, ValueError):
                total_results = 0

        total_pages = (
            math.ceil(total_results / self.PAGE_SIZE)
            if total_results
            else (1 if items else 0)
        )

        return SearchResult(
            items=items,
            page=page,
            total_pages=total_pages,
            total_results=total_results,
            source="omdb",
        )
