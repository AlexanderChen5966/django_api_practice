"""Public weather API views."""

from asgiref.sync import async_to_sync
from django.http import JsonResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ForecastQuery
from .services import WeatherService


def providers(request):
    """Return metadata about supported weather providers."""

    return JsonResponse(
        {
            "providers": [
                {
                    "id": "cwa",
                    "name": "CWA 36h",
                    "params": ["locationName"],
                    "default": True,
                },
                {
                    "id": "owm",
                    "name": "OpenWeatherMap 5d/3h",
                    "params": ["city", "country", "lang", "units"],
                },
            ]
        }
    )


class ForecastView(APIView):
    """Return a normalized forecast from the weather service."""

    @extend_schema(
        parameters=[
            OpenApiParameter(name="provider", required=False, type=str),
            OpenApiParameter(name="locationName", required=False, type=str),
            OpenApiParameter(name="city", required=False, type=str),
            OpenApiParameter(name="country", required=False, type=str),
            OpenApiParameter(name="lang", required=False, type=str),
            OpenApiParameter(name="units", required=False, type=str),
        ],
        responses={200: dict},
    )
    def get(self, request):
        query = ForecastQuery(data=request.query_params)
        query.is_valid(raise_exception=True)

        service = WeatherService()
        forecast = async_to_sync(service.get_forecast)(**query.validated_data)

        payload = {
            "location": {
                "name": forecast.location_name,
                "country": forecast.country,
            },
            "units": forecast.units,
            "source": forecast.source,
            "periods": [vars(period) for period in forecast.periods],
        }

        return Response(payload)
