import pytest


@pytest.mark.django_db
def test_movies_providers(client):
    response = client.get("/api/v1/movie/providers")
    assert response.status_code == 200

    payload = response.json()
    assert "providers" in payload
    assert any(item["id"] == "tmdb" for item in payload["providers"])


@pytest.mark.django_db
def test_movies_search_requires_query(client):
    response = client.get("/api/v1/movies/search")
    assert response.status_code in (400, 422)
