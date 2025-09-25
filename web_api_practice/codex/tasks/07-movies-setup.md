# 07-movies-setup.md

## 目標
- 建立 `apps/movies` 架構（模式A：Domain app + 多 adapters）
- 新增環境變數：`OMDB_API_KEY`, `TMDB_API_KEY`, `TMDB_IMAGE_BASE`
- 註冊 `apps.movies`、掛上路由 `/api/v1/movie/providers`（先提供最小可用回應）
- 保持與既有規格一致（DRF、drf-spectacular、httpx、Cache/重試/降級）

## 指令

```bash
# 1) 新增環境變數（.env.example/.env）
applypatch << 'EOF'
*** Begin Patch
*** Update File: .env.example
@@
 OWM_API_KEY=put-your-openweather-key
 CWA_API_KEY=put-your-cwa-key
 HTTP_DEFAULT_TIMEOUT=8.0
 HTTP_MAX_RETRIES=2
 REDIS_URL=redis://localhost:6379/0
+OMDB_API_KEY=put-your-omdb-key
+TMDB_API_KEY=put-your-tmdb-key
+TMDB_IMAGE_BASE=https://image.tmdb.org/t/p/w500
*** End Patch
EOF
cp .env.example .env

# 2) settings.py：註冊 apps.movies
applypatch << 'EOF'
*** Begin Patch
*** Update File: web_api_practice/web_api_practice/settings.py
@@
 INSTALLED_APPS += ["apps.movies"]
*** End Patch
EOF

# 3) urls.py：掛上 movies 路由
applypatch << 'EOF'
*** Begin Patch
*** Update File: web_api_practice/web_api_practice/urls.py
@@
 urlpatterns = [
@@
-    path("api/v1/", include("apps.weather.urls")),
+    path("api/v1/", include("apps.weather.urls")),
+    path("api/v1/", include("apps.movies.urls")),
 ]
*** End Patch
EOF

# 4) 建立 movies 骨架
mkdir -p apps/movies/adapters
touch apps/movies/__init__.py apps/movies/apps.py apps/movies/urls.py apps/movies/views.py apps/movies/serializers.py apps/movies/services.py apps/movies/schemas.py apps/movies/adapters/__init__.py apps/movies/adapters/base.py

cat > apps/movies/apps.py << 'EOF'
from django.apps import AppConfig
class MoviesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.movies"
EOF

cat > apps/movies/urls.py << 'EOF'
from django.urls import path
from . import views
urlpatterns = [
    path("movie/providers", views.movie_providers, name="movie_providers"),
]
EOF

cat > apps/movies/views.py << 'EOF'
from django.http import JsonResponse
def movie_providers(request):
    return JsonResponse({
        "providers":[
            {"id":"tmdb","name":"The Movie Database","params":["query","page","lang"],"default":True},
            {"id":"omdb","name":"OMDb","params":["query","page"]}
        ]
    })
EOF
```

## 驗收
- `/api/v1/movie/providers` 回傳 providers JSON
- `INSTALLED_APPS` 已包含 `apps.movies`
