"""Base contract for movie search adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..schemas import SearchResult


class BaseMoviesAdapter(ABC):
    """Define the interface every movie provider must implement."""

    @abstractmethod
    async def search(self, **kwargs) -> SearchResult:
        """Return a normalized ``SearchResult`` built from provider data."""

