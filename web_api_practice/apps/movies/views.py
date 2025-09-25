from django.http import JsonResponse


def movie_providers(request):
    return JsonResponse(
        {
            "providers": [
                {
                    "id": "tmdb",
                    "name": "The Movie Database",
                    "params": ["query", "page", "lang"],
                    "default": True,
                },
                {
                    "id": "omdb",
                    "name": "OMDb",
                    "params": ["query", "page"],
                },
            ]
        }
    )
