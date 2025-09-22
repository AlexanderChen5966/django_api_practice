"""Weather adapter package exports."""

from .base import BaseWeatherAdapter
from .cwa36h import Cwa36hAdapter
from .openweather import OpenWeatherAdapter

__all__ = [
    "BaseWeatherAdapter",
    "Cwa36hAdapter",
    "OpenWeatherAdapter",
]

