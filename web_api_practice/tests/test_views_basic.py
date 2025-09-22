"""Basic integration tests for weather API endpoints."""

import pytest

from apps.weather.schemas import Forecast, Period


@pytest.mark.django_db
def test_providers_endpoint(client):
    response = client.get("/api/v1/providers")

    assert response.status_code == 200
    payload = response.json()
    assert "providers" in payload
    assert any(item["id"] == "cwa" for item in payload["providers"])


@pytest.mark.django_db
def test_forecast_endpoint_returns_normalized_payload(client, monkeypatch):
    class StubService:
        async def get_forecast(self, **kwargs):
            return Forecast(
                location_name="Taipei",
                country="TW",
                units="metric",
                source="owm",
                periods=[
                    Period(
                        ts="2025-09-22T00:00:00+00:00",
                        temp=24.0,
                        desc="clear sky",
                        humidity=70,
                        wind_kph=10.8,
                    )
                ],
            )

    monkeypatch.setattr("apps.weather.views.WeatherService", StubService)

    response = client.get(
        "/api/v1/weather/forecast",
        {"city": "Taipei", "country": "TW"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "owm"
    assert len(data["periods"]) == 1
    assert data["periods"][0]["temp"] == 24.0
