# 09-movies-adapters-service-views.md

## 目標
- 完成 `BaseMoviesAdapter`、`TmdbAdapter`、`OmdbAdapter`
- 完成 `MoviesService.search()`（快取、預設 TMDb、降級 OMDb）
- 完成 `GET /api/v1/movies/search` 與 Swagger 註解

## 指令
```bash
# 1) adapters/base.py
applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/movies/adapters/base.py
@@
 from abc import ABC, abstractmethod
 from ..schemas import SearchResult

 class BaseMoviesAdapter(ABC):
     @abstractmethod
     async def search(self, **kwargs) -> SearchResult:
         ...
*** End Patch
EOF
```

```bash
# 2) TMDb Adapter
cat > apps/movies/adapters/tmdb.py << 'EOF'
import httpx
from django.conf import settings
from ...common.http import get as http_get
from ..schemas import Movie, SearchResult
from .base import BaseMoviesAdapter

class TmdbAdapter(BaseMoviesAdapter):
    BASE = "https://api.themoviedb.org/3/search/movie"

    async def search(self, *, query: str, page: int = 1, lang: str = "zh-TW") -> SearchResult:
        params = {"api_key": settings.TMDB_API_KEY, "query": query, "page": page, "language": lang}
        async with httpx.AsyncClient(timeout=settings.HTTP_DEFAULT_TIMEOUT) as client:
            r = await http_get(client, self.BASE, params=params)
            data = r.json()
        img_base = getattr(settings, "TMDB_IMAGE_BASE", "https://image.tmdb.org/t/p/w500")
        items = []
        for it in data.get("results", []) or []:
            poster = it.get("poster_path")
            items.append(Movie(
                id=str(it.get("id","")),
                title=it.get("title",""),
                year=(it.get("release_date","")[:4] or None),
                plot=it.get("overview"),
                poster=(f"{img_base}{poster}" if poster else None),
                genres=it.get("genre_ids"),
                rating=it.get("vote_average"),
                source="tmdb"
            ))
        return SearchResult(
            items=items,
            page=int(data.get("page",1)),
            total_pages=int(data.get("total_pages",1)),
            total_results=int(data.get("total_results",len(items))),
            source="tmdb"
        )
EOF
```

```bash
# 3) OMDb Adapter
cat > apps/movies/adapters/omdb.py << 'EOF'
import httpx, math
from django.conf import settings
from ...common.http import get as http_get
from ..schemas import Movie, SearchResult
from .base import BaseMoviesAdapter

class OmdbAdapter(BaseMoviesAdapter):
    BASE = "https://www.omdbapi.com/"

    async def search(self, *, query: str, page: int = 1) -> SearchResult:
        params = {"apikey": settings.OMDB_API_KEY, "s": query, "type": "movie", "page": page}
        async with httpx.AsyncClient(timeout=settings.HTTP_DEFAULT_TIMEOUT) as client:
            r = await http_get(client, self.BASE, params=params)
            data = r.json()

        items = []
        for it in data.get("Search", []) or []:
            poster = it.get("Poster")
            items.append(Movie(
                id=it.get("imdbID",""),
                title=it.get("Title",""),
                year=it.get("Year"),
                poster=None if (poster in (None,"N/A")) else poster,
                source="omdb"
            ))
        total = int(data.get("totalResults","0")) if data.get("totalResults") else 0
        total_pages = math.ceil(total/10) if total else (1 if items else 0)
        return SearchResult(items=items, page=page, total_pages=total_pages, total_results=total, source="omdb")
EOF
```

```bash
# 4) MoviesService
applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/movies/services.py
@@
 from django.core.cache import cache
 from typing import Any
 from .adapters.tmdb import TmdbAdapter
 from .adapters.omdb import OmdbAdapter

 class MoviesService:
     def __init__(self):
         self.tmdb = TmdbAdapter()
         self.omdb = OmdbAdapter()

     def _key(self, provider: str, kwargs: dict) -> str:
         return "movies:%s:%s" % (provider, ",".join(f"{k}={kwargs[k]}" for k in sorted(kwargs.keys())))

     async def search(self, *, provider: str | None = None, **kwargs: Any):
         chosen = provider or "tmdb"
         key = self._key(chosen, kwargs)
         hit = cache.get(key)
         if hit: return hit
         try:
             if chosen == "tmdb":
                 res = await self.tmdb.search(**kwargs)
             elif chosen == "omdb":
                 res = await self.omdb.search(**kwargs)
             else:
                 raise ValueError("Unknown provider")
         except Exception:
             # 降級：tmdb -> omdb
             fallback = "omdb" if chosen == "tmdb" else "tmdb"
             res = await (self.omdb.search(**kwargs) if fallback=="omdb" else self.tmdb.search(**kwargs))
         cache.set(key, res, 300)
         return res
*** End Patch
EOF
```

```bash
# 5) Views + URLs + Swagger
applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/movies/views.py
@@
-from django.http import JsonResponse
+from django.http import JsonResponse
+from rest_framework.views import APIView
+from rest_framework.response import Response
+from drf_spectacular.utils import extend_schema, OpenApiParameter
+from .serializers import MoviesSearchQuery
+from .services import MoviesService
@@
 def movie_providers(request):
@@
     })
+
+class MoviesSearchView(APIView):
+    @extend_schema(
+        parameters=[
+            OpenApiParameter(name="query", required=True, type=str),
+            OpenApiParameter(name="provider", required=False, type=str),
+            OpenApiParameter(name="page", required=False, type=int),
+            OpenApiParameter(name="lang", required=False, type=str),
+        ],
+        responses={200: dict},
+    )
+    async def get(self, request):
+        q = MoviesSearchQuery(data=request.query_params)
+        q.is_valid(raise_exception=True)
+        svc = MoviesService()
+        data = await svc.search(**q.validated_data)
+        return Response({
+            "source": data.source,
+            "page": data.page,
+            "total_pages": data.total_pages,
+            "total_results": data.total_results,
+            "items": [vars(m) for m in data.items]
+        })
*** End Patch
EOF
```

```bash
applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/movies/urls.py
@@
-from django.urls import path
-from . import views
-urlpatterns = [
-    path("movie/providers", views.movie_providers, name="movie_providers"),
-]
+from django.urls import path
+from . import views
+urlpatterns = [
+    path("movie/providers", views.movie_providers, name="movie_providers"),
+    path("movies/search", views.MoviesSearchView.as_view(), name="movies_search"),
+]
*** End Patch
EOF
```

## 驗收
- `/api/v1/movies/search?query=Inception&provider=tmdb&page=1&lang=zh-TW` 200
- `/api/v1/movies/search?query=Inception&provider=omdb&page=1` 200
- 未指定 provider → 預設 tmdb；tmdb 出錯時能降級 omdb
