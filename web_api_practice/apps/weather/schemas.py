from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Period:
    ts: str  # ISO8601 UTC timestamp
    temp: float
    desc: str
    humidity: Optional[int] = None
    wind_kph: Optional[float] = None


@dataclass
class Forecast:
    location_name: str
    country: str
    units: str  # "metric" | "imperial"
    source: str  # "owm" | "cwa"
    periods: List[Period]
