import httpx
import backoff
from django.conf import settings

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


@backoff.on_exception(
    backoff.expo,
    (
        httpx.ReadTimeout,
        httpx.ConnectTimeout,
        httpx.RemoteProtocolError,
        httpx.HTTPStatusError,
    ),
    max_tries=1 + int(getattr(settings, "HTTP_MAX_RETRIES", 2)),
)
async def get(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    response = await client.get(url, **kwargs)
    if response.status_code in RETRYABLE_STATUS:
        response.raise_for_status()
    return response
