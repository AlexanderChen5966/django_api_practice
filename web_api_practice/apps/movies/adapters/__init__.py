"""Movies adapters package exports."""

from .base import BaseMoviesAdapter
from .omdb import OmdbAdapter
from .tmdb import TmdbAdapter

__all__ = [
    "BaseMoviesAdapter",
    "OmdbAdapter",
    "TmdbAdapter",
]

