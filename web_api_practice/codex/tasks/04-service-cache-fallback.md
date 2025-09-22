# 04-service-cache-fallback.md

## 目標
- `WeatherService`：快取、選擇 provider、預設多源策略、降級與重試映射

## 指令與內容
```bash
applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/weather/services.py
@@
-from django.conf import settings
+from django.conf import settings
+from typing import Any
+from django.core.cache import cache
+from .adapters.openweather import OpenWeatherAdapter
+from .adapters.cwa36h import Cwa36hAdapter
+
+class WeatherService:
+    def __init__(self):
+        self.owm = OpenWeatherAdapter()
+        self.cwa = Cwa36hAdapter()
+
+    def _cache_key(self, provider: str, kwargs: dict) -> str:
+        items = ",".join(f"{k}={kwargs[k]}" for k in sorted(kwargs.keys()))
+        return f"forecast:{provider}:{items}"
+
+    async def get_forecast(self, *, provider: str | None = None, **kwargs: Any):
+        # 1) provider 決策
+        chosen = provider
+        if not chosen:
+            if "locationName" in kwargs:
+                chosen = "cwa"
+            elif "city" in kwargs and "country" in kwargs:
+                chosen = "owm"
+            else:
+                raise ValueError("Missing required params to decide provider.")
+
+        # 2) 快取
+        key = self._cache_key(chosen, kwargs)
+        val = cache.get(key)
+        if val:
+            return val
+
+        # 3) 呼叫與降級
+        try:
+            if chosen == "owm":
+                val = await self.owm.fetch_forecast(**kwargs)
+            elif chosen == "cwa":
+                val = await self.cwa.fetch_forecast(**kwargs)
+            else:
+                raise ValueError("Unknown provider")
+        except Exception:
+            # 簡易降級策略
+            if chosen == "cwa" and "city" in kwargs and "country" in kwargs:
+                val = await self.owm.fetch_forecast(city=kwargs["city"], country=kwargs["country"], lang=kwargs.get("lang","zh_tw"), units=kwargs.get("units","metric"))
+            elif chosen == "owm" and "locationName" in kwargs:
+                val = await self.cwa.fetch_forecast(locationName=kwargs["locationName"])
+            else:
+                raise
+
+        cache.set(key, val, timeout=300)
+        return val
*** End Patch
EOF
```
