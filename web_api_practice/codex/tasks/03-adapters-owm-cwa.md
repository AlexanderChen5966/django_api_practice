# 03-adapters-owm-cwa.md

## 目標
- 完成 `BaseWeatherAdapter`
- 完成 `OpenWeatherAdapter` 與 `Cwa36hAdapter`（轉換為統一模型）

## 指令與內容
```bash
applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/weather/adapters/base.py
@@
-from abc import ABC, abstractmethod
-from ..schemas import Forecast
+from abc import ABC, abstractmethod
+from ..schemas import Forecast

 class BaseWeatherAdapter(ABC):
     @abstractmethod
     async def fetch_forecast(self, **kwargs) -> Forecast:
-        ...
+        ...
*** End Patch
EOF
```
```bash
cat > apps/weather/adapters/openweather.py << 'EOF'
import httpx
from django.conf import settings
from .base import BaseWeatherAdapter
from ...common.http import get as http_get
from ..schemas import Forecast, Period
from ...common.utils import to_iso_utc

class OpenWeatherAdapter(BaseWeatherAdapter):
    BASE = "https://api.openweathermap.org/data/2.5/forecast"

    async def fetch_forecast(self, *, city: str, country: str, lang="zh_tw", units="metric") -> Forecast:
        params = {"q": f"{city},{country}", "APPID": settings.OWM_API_KEY, "lang": lang, "units": units}
        async with httpx.AsyncClient(timeout=settings.HTTP_DEFAULT_TIMEOUT) as client:
            r = await http_get(client, self.BASE, params=params)
            data = r.json()
        periods = []
        for it in data.get("list", []):
            ts = it.get("dt_txt") or ""
            periods.append(Period(
                ts=to_iso_utc(ts),
                temp=float(it["main"]["temp"]),
                desc=it["weather"][0]["description"],
                humidity=it["main"].get("humidity"),
                wind_kph=(it["wind"].get("speed", 0.0) * 3.6) if it.get("wind") else None
            ))
        return Forecast(location_name=city, country=country, units=units, source="owm", periods=periods)
EOF
```
```bash
cat > apps/weather/adapters/cwa36h.py << 'EOF'
import httpx
from django.conf import settings
from .base import BaseWeatherAdapter
from ...common.http import get as http_get
from ..schemas import Forecast, Period

class Cwa36hAdapter(BaseWeatherAdapter):
    BASE = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

    async def fetch_forecast(self, *, locationName: str, units="metric") -> Forecast:
        params = {"Authorization": settings.CWA_API_KEY, "locationName": locationName}
        async with httpx.AsyncClient(timeout=settings.HTTP_DEFAULT_TIMEOUT) as client:
            r = await http_get(client, self.BASE, params=params)
            data = r.json()

        loc = data["records"]["location"][0]
        name = loc["locationName"]
        elements = {e["elementName"]: e["time"] for e in loc["weatherElement"]}
        wx = elements.get("Wx", [])
        t = elements.get("T", [])

        periods = []
        for i in range(min(len(wx), len(t))):
            w = wx[i]
            temp = t[i]["parameter"]["parameterName"]
            periods.append(Period(
                ts=w["startTime"],
                temp=float(temp),
                desc=w["parameter"]["parameterName"],
            ))
        return Forecast(location_name=name, country="TW", units=units, source="cwa", periods=periods)
EOF
```
