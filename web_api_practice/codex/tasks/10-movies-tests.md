# 10-movies-tests.md

## 目標
- 基本測試（providers list / search 參數缺失）
- （可擴充）使用 httpx-mock 模擬上游

## 指令
```bash
mkdir -p tests
cat > tests/test_movies_views.py << 'EOF'
import pytest

@pytest.mark.django_db
def test_movies_providers(client):
    r = client.get("/api/v1/movie/providers")
    assert r.status_code == 200
    js = r.json()
    assert "providers" in js and any(p["id"]=="tmdb" for p in js["providers"])

@pytest.mark.django_db
def test_movies_search_requires_query(client):
    r = client.get("/api/v1/movies/search")
    assert r.status_code in (400,422)
EOF
```

## 驗收
- 測試可執行：`pytest -q`
