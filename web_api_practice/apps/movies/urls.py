from django.urls import path

from . import views

urlpatterns = [
    path("movie/providers", views.movie_providers, name="movie_providers"),
    path("movies/search", views.MoviesSearchView.as_view(), name="movies_search"),
]
