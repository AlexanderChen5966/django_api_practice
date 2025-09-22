"""Weather application routing."""

from django.urls import path

from . import views


urlpatterns = [
    path("providers", views.providers, name="providers"),
    path("weather/forecast", views.ForecastView.as_view(), name="forecast"),
]
