# 使用Django 串接API 練習

練習以Django 串接API，整合各種API資料，會陸續更新 
1. OpenWeatherMap (OWM) 與中央氣象署 (CWA) 的天氣資料，提供單一且一致的天氣預報介面。
2. TMDb 與 OMDb 的電影查詢，統一出 `Movie` 與 `SearchResult` 資料模型。


服務內建快取、備援策略與自動化測試，方便擴充新的資料來源。


## 架構概述

- **Web Framework**：Django 5 + Django REST Framework，並以 drf-spectacular 產生 OpenAPI/Swagger 文件。
- **領域分層**：
  - `apps/weather/services.py`：協調快取、資料來源挑選與備援流程的應用服務層。
  - `apps/weather/adapters/*.py`：以 Adapter Pattern 封裝各上游提供者，輸出統一的 `Forecast` 領域模型。
  - `apps/weather/views.py` / `serializers.py`：負責 API 輸入輸出驗證與回應。
  - `apps/movies/services.py`：處理電影搜尋快取、提供者選擇與降級邏輯。
  - `apps/movies/adapters/*.py`：包裝 TMDb、OMDb 查詢流程並回傳統一的 `Movie`、`SearchResult`。
  - `apps/movies/views.py` / `serializers.py`：驗證查詢參數並輸出統一格式。
  - `apps/common/`：集中快取、HTTP 請求與例外處理等基礎設施。
- **資料提取與穩定性**：透過 httpx.AsyncClient + backoff 實作重試與逾時控制；快取使用 Django Cache (可搭配 redis) 以降低上游負載。
- **設定管理**：以 `.env` 檔提供 API Key、逾時與重試等參數，支援不同部署環境。

專案主要結構：
```
web_api_practice/
├─ apps/
│  ├─ common/            # 快取、HTTP、例外與通用工具
│  ├─ weather/           # 天氣領域 (adapters, services, views, schemas)
│  └─ movies/            # 電影領域 (adapters, services, views, schemas)
├─ tests/                # Pytest 測試
├─ manage.py
└─ requirements.txt
```

## 環境準備

1. 建立虛擬環境並安裝依賴：
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r web_api_practice/requirements.txt
   ```

2. 初始化環境變數：
   ```bash
   cp web_api_practice/.env.example web_api_practice/.env
   ```
   必填參數：
   - `OWM_API_KEY`：OpenWeatherMap API Key。
   - `CWA_API_KEY`：中央氣象署資料平臺授權碼。
   - `TMDB_API_KEY`：The Movie Database API Key。
   - `OMDB_API_KEY`：OMDb API Key。
   - `TMDB_IMAGE_BASE`：TMDb 圖片網址基底（預設 `https://image.tmdb.org/t/p/w500`，可自行調整尺寸）。
   - `HTTP_DEFAULT_TIMEOUT`、`HTTP_MAX_RETRIES`：可選，用於調整 HTTP 行為。

3. 執行資料庫遷移並啟動開發伺服器：
   ```bash
   python web_api_practice/manage.py migrate
   python web_api_practice/manage.py runserver
   ```

## API 說明

- `GET /api/v1/providers`：列出可用資料來源與其必填查詢參數。
- `GET /api/v1/weather/forecast`：取得統一格式的天氣預報。  
  - OWM：提供 `city` 與 `country`。
  - CWA：提供 `locationName`（或 `location_name`）。
  - 服務內建快取與備援，並會輸出一致的時間區段資料。
- `GET /api/v1/movie/providers`：列出已註冊的電影搜尋提供者與支援的查詢參數。
- `GET /api/v1/movies/search`：搜尋電影，預設使用 TMDb，若失敗將降級至 OMDb。  
  - `query` 為必填。
  - 可選 `provider=tmdb|omdb`、`page`、`lang` (TMDb 專用)。
- Swagger UI：`GET /api/docs/`。

## 測試

```bash
cd web_api_practice
pytest -q
```

現行單元測試涵蓋：
- `tests/test_weather_views.py`：天氣查詢流程與序列化。
- `tests/test_movies_views.py`：電影提供者列表與查詢參數驗證。

框架內建檢查：
```bash
python manage.py check
```

## Logging 與營運建議

- 於 Django `LOGGING` 增加 `apps.weather` 的 `StreamHandler` (INFO) 監控上游請求與備援情況，並針對錯誤/警告設計告警。
- 觀測快取命中率（可搭配 Prometheus / OpenTelemetry）來追蹤上游穩定度。
- 部署時可透過環境變數調整逾時與重試，並以 APM 工具監測效能。
- 排程定期煙霧測試，透過兩個提供者呼叫 `/api/v1/weather/forecast` 驗證金鑰與服務可用性。
