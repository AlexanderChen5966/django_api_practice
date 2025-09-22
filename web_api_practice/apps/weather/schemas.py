"""Domain schemas for weather forecasts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass
class OWMPeriod:
    """Normalized period entry from OpenWeatherMap."""

    ts: str  # ISO8601 UTC timestamp
    temp: float
    desc: str
    humidity: Optional[int] = None
    wind_kph: Optional[float] = None


@dataclass
class CWAPeriod:
    """Normalized period entry from CWA 36-hour dataset."""

    start: str  # ISO8601 UTC start timestamp
    end: Optional[str]
    desc: str
    pop: Optional[int] = None
    min_temp: Optional[float] = None
    max_temp: Optional[float] = None
    avg_temp: Optional[float] = None
    comfort: Optional[str] = None


Period = Union[OWMPeriod, CWAPeriod]


@dataclass
class Forecast:
    location_name: str
    country: str
    units: str  # "metric" | "imperial"
    source: str  # "owm" | "cwa"
    periods: list[Period] = field(default_factory=list)

