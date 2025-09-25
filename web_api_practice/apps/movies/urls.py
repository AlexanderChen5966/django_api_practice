from django.urls import path

from . import views

urlpatterns = [
    path("movie/providers", views.movie_providers, name="movie_providers"),
]
