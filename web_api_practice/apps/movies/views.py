from dataclasses import asdict

from asgiref.sync import async_to_sync
from django.http import JsonResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import MoviesSearchQuery
from .services import MoviesService


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


class MoviesSearchView(APIView):
    """Handle movie search requests across providers."""

    service_class = MoviesService

    @extend_schema(
        parameters=[
            OpenApiParameter(name="query", required=True, type=str),
            OpenApiParameter(name="provider", required=False, type=str),
            OpenApiParameter(name="page", required=False, type=int),
            OpenApiParameter(name="lang", required=False, type=str),
        ],
        responses={200: dict},
    )
    def get(self, request):
        serializer = MoviesSearchQuery(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        service = self.service_class()
        result = async_to_sync(service.search)(**serializer.validated_data)

        return Response(
            {
                "source": result.source,
                "page": result.page,
                "total_pages": result.total_pages,
                "total_results": result.total_results,
                "items": [asdict(movie) for movie in result.items],
            }
        )
