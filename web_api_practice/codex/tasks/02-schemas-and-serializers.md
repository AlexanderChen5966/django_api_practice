# 02-schemas-and-serializers.md

## 目標
- 定義統一資料模型 `Period`、`Forecast`
- 定義查詢參數 `ForecastQuery`（provider 條件）

## 指令與內容
```bash
applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/weather/schemas.py
@@
-from dataclasses import dataclass
-from typing import List, Optional
+from dataclasses import dataclass
+from typing import List, Optional

 @dataclass
 class Period:
-    pass
+    ts: str                 # ISO8601 UTC
+    temp: float
+    desc: str
+    humidity: Optional[int] = None
+    wind_kph: Optional[float] = None

 @dataclass
 class Forecast:
-    pass
+    location_name: str
+    country: str
+    units: str              # "metric" | "imperial"
+    source: str             # "owm" | "cwa"
+    periods: List[Period] = None
*** End Patch
EOF
```
```bash
applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/weather/serializers.py
@@
-from rest_framework import serializers
+from rest_framework import serializers
+
+class ForecastQuery(serializers.Serializer):
+    # OWM
+    city = serializers.CharField(required=False)
+    country = serializers.CharField(required=False)
+    lang = serializers.CharField(required=False, default="zh_tw")
+    units = serializers.ChoiceField(choices=["metric","imperial"], required=False, default="metric")
+    # CWA
+    locationName = serializers.CharField(required=False)
+    # Provider
+    provider = serializers.ChoiceField(choices=["owm","cwa"], required=False)
+
+    def validate(self, attrs):
+        provider = attrs.get("provider")
+        if provider == "cwa":
+            if not attrs.get("locationName"):
+                raise serializers.ValidationError("locationName is required when provider=cwa")
+        elif provider == "owm":
+            if not attrs.get("city") or not attrs.get("country"):
+                raise serializers.ValidationError("city and country are required when provider=owm")
+        else:
+            # 未指定 provider 時，允許任一組參數，交由 service 做預設策略
+            if not (attrs.get("locationName") or (attrs.get("city") and attrs.get("country"))):
+                raise serializers.ValidationError("Provide locationName (CWA) or city+country (OWM).")
+        return attrs
*** End Patch
EOF
```
