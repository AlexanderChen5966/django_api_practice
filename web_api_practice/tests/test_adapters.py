"""Unit tests for weather adapter normalization logic."""

import pytest

from apps.weather.adapters.cwa36h import Cwa36hAdapter
from apps.weather.adapters.openweather import OpenWeatherAdapter
from apps.weather.schemas import CWAPeriod, OWMPeriod


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_openweather_adapter_normalizes_payload(monkeypatch):
    payload = {
        "city": {"name": "Taipei", "country": "TW"},
        "list": [
            {
                "dt_txt": "2025-09-22 00:00:00",
                "main": {"temp": 23.5, "humidity": 65},
                "weather": [{"description": "few clouds"}],
                "wind": {"speed": 2.0},
            }
        ],
    }

    async def fake_http_get(client, url, params=None):
        assert "openweathermap" in url
        return DummyResponse(payload)

    monkeypatch.setattr(
        "apps.weather.adapters.openweather.http_get",
        fake_http_get,
    )

    adapter = OpenWeatherAdapter()
    forecast = await adapter.fetch_forecast(city="Taipei", country="TW")

    assert forecast.source == "owm"
    assert forecast.location_name == "Taipei"
    assert isinstance(forecast.periods[0], OWMPeriod)
    assert forecast.periods[0].desc == "few clouds"
    assert forecast.periods[0].wind_kph == pytest.approx(7.2)


@pytest.mark.asyncio
async def test_cwa_adapter_maps_elements(monkeypatch):
    payload = {
        "records": {
            "location": [
                {
                    "locationName": "臺北市",
                    "weatherElement": [
                        {
                            "elementName": "Wx",
                            "time": [
                                {
                                    "startTime": "2025-09-22 18:00:00",
                                    "parameter": {"parameterName": "陰短暫陣雨或雷雨"},
                                }
                            ],
                        },
                        {
                            "elementName": "PoP",
                            "time": [
                                {
                                    "startTime": "2025-09-22 18:00:00",
                                    "parameter": {"parameterName": "60"},
                                }
                            ],
                        },
                        {
                            "elementName": "MinT",
                            "time": [
                                {
                                    "startTime": "2025-09-22 18:00:00",
                                    "parameter": {"parameterName": "28"},
                                }
                            ],
                        },
                        {
                            "elementName": "MaxT",
                            "time": [
                                {
                                    "startTime": "2025-09-22 18:00:00",
                                    "parameter": {"parameterName": "30"},
                                }
                            ],
                        },
                        {
                            "elementName": "CI",
                            "time": [
                                {
                                    "startTime": "2025-09-22 18:00:00",
                                    "parameter": {"parameterName": "悶熱"},
                                }
                            ],
                        },
                    ],
                }
            ]
        }
    }

    async def fake_http_get(client, url, params=None):
        assert "opendata.cwa.gov.tw" in url
        return DummyResponse(payload)

    monkeypatch.setattr("apps.weather.adapters.cwa36h.http_get", fake_http_get)

    adapter = Cwa36hAdapter()
    forecast = await adapter.fetch_forecast(location_name="臺北市")

    assert forecast.source == "cwa"
    assert forecast.location_name == "臺北市"
    first_period = forecast.periods[0]
    assert isinstance(first_period, CWAPeriod)
    assert first_period.desc == "陰短暫陣雨或雷雨"
    assert first_period.pop == 60
    assert first_period.min_temp == pytest.approx(28.0)
    assert first_period.max_temp == pytest.approx(30.0)
    assert first_period.avg_temp == pytest.approx(29.0)
    assert first_period.comfort == "悶熱"
