# 05-views-urls-swagger.md

## 目標
- 對外端點：`GET /api/v1/weather/forecast` 與 `GET /api/v1/providers`
- 加上 drf-spectacular 註解

## 指令與內容
```bash
applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/weather/views.py
@@
-from django.http import JsonResponse
-def providers(request):
-    return JsonResponse({
-        "providers": [
-            {"id": "cwa", "name": "CWA 36h", "params": ["locationName"], "default": True},
-            {"id": "owm", "name": "OpenWeatherMap 5d/3h", "params": ["city","country","lang","units"]},
-        ]
-    })
+from django.http import JsonResponse
+from rest_framework.views import APIView
+from rest_framework.response import Response
+from drf_spectacular.utils import extend_schema, OpenApiParameter
+from .serializers import ForecastQuery
+from .services import WeatherService
+
+def providers(request):
+    return JsonResponse({
+        "providers": [
+            {"id": "cwa", "name": "CWA 36h", "params": ["locationName"], "default": True},
+            {"id": "owm", "name": "OpenWeatherMap 5d/3h", "params": ["city","country","lang","units"]},
+        ]
+    })
+
+class ForecastView(APIView):
+    @extend_schema(
+        parameters=[
+            OpenApiParameter(name="provider", required=False, type=str),
+            OpenApiParameter(name="locationName", required=False, type=str),
+            OpenApiParameter(name="city", required=False, type=str),
+            OpenApiParameter(name="country", required=False, type=str),
+            OpenApiParameter(name="lang", required=False, type=str),
+            OpenApiParameter(name="units", required=False, type=str),
+        ],
+        responses={200: dict},
+    )
+    async def get(self, request):
+        q = ForecastQuery(data=request.query_params)
+        q.is_valid(raise_exception=True)
+        svc = WeatherService()
+        data = await svc.get_forecast(**q.validated_data)
+        resp = {
+            "location": {"name": data.location_name, "country": data.country},
+            "units": data.units,
+            "source": data.source,
+            "periods": [vars(p) for p in data.periods or []],
+        }
+        return Response(resp)
*** End Patch
EOF
```
```bash
applypatch << 'EOF'
*** Begin Patch
*** Update File: apps/weather/urls.py
@@
-from django.urls import path
-from . import views
-urlpatterns = [
-    path("providers", views.providers, name="providers"),
-]
+from django.urls import path
+from . import views
+urlpatterns = [
+    path("providers", views.providers, name="providers"),
+    path("weather/forecast", views.ForecastView.as_view(), name="forecast"),
+]
*** End Patch
EOF
```
