from django.core.cache import cache


def get_cache(key: str):
    return cache.get(key)


def set_cache(key: str, value, timeout: int = 300):
    cache.set(key, value, timeout=timeout)
