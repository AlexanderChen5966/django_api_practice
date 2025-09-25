from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Movie:
    id: str
    title: str
    year: Optional[str] = None
    plot: Optional[str] = None
    poster: Optional[str] = None
    genres: Optional[List[int]] = None
    rating: Optional[float] = None
    source: str = "tmdb"


@dataclass
class SearchResult:
    items: List[Movie]
    page: int
    total_pages: int
    total_results: int
    source: str
