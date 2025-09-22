from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OWMPeriod:
    ts: str  # ISO8601 UTC timestamp
    temp: float
    desc: str
    humidity: Optional[int] = None
    wind_kph: Optional[float] = None

class CWAPeriod:
    ts: str  # ISO8601 UTC timestamp
    desc: str
    pop: str
    minT: str
    maxT: str
    ci: str


@dataclass
class Forecast:
    location_name: str
    country: str
    units: str  # "metric" | "imperial"
    source: str  # "owm" | "cwa"
    periods: List[OWMPeriod]
