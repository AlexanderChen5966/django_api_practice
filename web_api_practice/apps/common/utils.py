from datetime import datetime, timezone


def to_iso_utc(dt_str: str) -> str:
    try:
        return (
            datetime.fromisoformat(dt_str.replace("Z", ""))
            .replace(tzinfo=timezone.utc)
            .isoformat()
        )
    except Exception:
        return dt_str
