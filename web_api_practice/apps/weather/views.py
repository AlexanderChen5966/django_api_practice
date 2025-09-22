from django.http import JsonResponse


def providers(request):
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
