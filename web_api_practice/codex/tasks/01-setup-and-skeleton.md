# 01-setup-and-skeleton.md

## 目標
- 建立虛擬環境與安裝必要套件
- 產生 `requirements.txt`、`.env.example`、`.env`
- 設定 DRF / drf-spectacular / Cache / ENV
- 建立 `apps/common` 與 `apps/weather` 的空骨架
- 新增 `/api/schema` 與 `/api/docs`

## 指令
```bash
# 進入專案根目錄（含 manage.py 的那層）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

cat > requirements.txt << 'EOF'
Django>=5.0
djangorestframework>=3.15
drf-spectacular>=0.27
httpx>=0.27
backoff>=2.2
python-dotenv>=1.0
pytest
pytest-django
pytest-asyncio
httpx-mock
responses
django-redis
EOF
pip install -r requirements.txt

cat > .env.example << 'EOF'
DJANGO_SETTINGS_MODULE=web_api_practice.settings
OWM_API_KEY=put-your-openweather-key
CWA_API_KEY=put-your-cwa-key
HTTP_DEFAULT_TIMEOUT=8.0
HTTP_MAX_RETRIES=2
REDIS_URL=redis://localhost:6379/0
EOF
cp .env.example .env

# 建立資料夾
mkdir -p apps/common
mkdir -p apps/weather/adapters
touch apps/__init__.py apps/common/__init__.py apps/weather/__init__.py apps/weather/adapters/__init__.py

# 初始 common
cat > apps/common/http.py << 'EOF'
import httpx, backoff
from django.conf import settings

RETRYABLE_STATUS = {429, 500, 502, 503, 504}

@backoff.on_exception(
    backoff.expo,
    (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError, httpx.HTTPStatusError),
    max_tries=1 + int(getattr(settings, "HTTP_MAX_RETRIES", 2)),
)
async def get(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    r = await client.get(url, **kwargs)
    if r.status_code in RETRYABLE_STATUS:
        r.raise_for_status()
    return r
EOF

cat > apps/common/cache.py << 'EOF'
from django.core.cache import cache
def get_cache(key: str):
    return cache.get(key)
def set_cache(key: str, value, timeout: int = 300):
    cache.set(key, value, timeout=timeout)
EOF

cat > apps/common/exceptions.py << 'EOF'
class UpstreamError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
EOF

cat > apps/common/utils.py << 'EOF'
from datetime import datetime, timezone
def to_iso_utc(dt_str: str) -> str:
    try:
        return datetime.fromisoformat(dt_str.replace("Z","")).replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        return dt_str
EOF

# 初始 weather (providers list 先可用)
cat > apps/weather/apps.py << 'EOF'
from django.apps import AppConfig
class WeatherConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.weather"
EOF

cat > apps/weather/urls.py << 'EOF'
from django.urls import path
from . import views
urlpatterns = [
    path("providers", views.providers, name="providers"),
]
EOF

cat > apps/weather/views.py << 'EOF'
from django.http import JsonResponse
def providers(request):
    return JsonResponse({
        "providers": [
            {"id": "cwa", "name": "CWA 36h", "params": ["locationName"], "default": True},
            {"id": "owm", "name": "OpenWeatherMap 5d/3h", "params": ["city","country","lang","units"]},
        ]
    })
EOF

cat > apps/weather/serializers.py << 'EOF'
# Phase 2 會補上 ForecastQuery
EOF

cat > apps/weather/services.py << 'EOF'
# Phase 4 會補上 WeatherService
EOF

cat > apps/weather/schemas.py << 'EOF'
# Phase 2 會補上 Period / Forecast dataclass
EOF

cat > apps/weather/adapters/base.py << 'EOF'
# Phase 3 會補上 BaseWeatherAdapter
EOF
```

## 手動編輯 settings.py / urls.py
- 在 `web_api_practice/web_api_practice/settings.py`：
  - 載入 dotenv、設定 INSTALLED_APPS 加入 `rest_framework`, `drf_spectacular`, `apps.common`, `apps.weather`
  - 設定 DRF Throttle、SPECTACULAR_SETTINGS、CACHES、ENV 讀取（OWM_API_KEY 等）
- 在 `web_api_practice/web_api_practice/urls.py`：
  - 加入 `/api/schema` 與 `/api/docs`
  - include `apps.weather.urls` 於 `/api/v1/`

## 驗收
```bash
python manage.py migrate
python manage.py runserver
# http://localhost:8000/api/docs 與 /api/v1/providers
```
