# 06-tests-and-ops.md

## 目標
- 基本測試：adapters / service / views
- 補充 README 與 logging 建議

## 指令與內容（建立最小測試）
```bash
mkdir -p tests
cat > tests/test_views_basic.py << 'EOF'
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_providers(client):
    resp = client.get("/api/v1/providers")
    assert resp.status_code == 200
    assert "providers" in resp.json()
EOF
```
```bash
pytest -q
```
