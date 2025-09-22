"""Base class for third-party weather adapters."""

from abc import ABC, abstractmethod

from ..schemas import Forecast


class BaseWeatherAdapter(ABC):
    """Common interface for fetching a normalized forecast."""

    @abstractmethod
    async def fetch_forecast(self, **kwargs) -> Forecast:
        """Return a unified ``Forecast`` built from the upstream provider."""

