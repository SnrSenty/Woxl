import re
from datetime import datetime, timedelta
from typing import Optional

_time_regex = re.compile(r"(?P<num>\d+)\s*(?P<unit>y|g|mon|мес|w|н|d|д|h|ч|m|м|s|с)$", re.IGNORECASE)


def parse_duration(text: str) -> Optional[timedelta]:
    """
    Parse durations like:
    10m/10м, 5s/5с, 2h/2ч, 3d/3д, 1w/1н, 1mon/1мес, 1y/1г
    Returns timedelta or None
    """
    s = text.strip().lower()
    m = _time_regex.match(s)
    if not m:
        return None
    num = int(m.group("num"))
    unit = m.group("unit")
    if unit in ("s", "с"):
        return timedelta(seconds=num)
    if unit in ("m", "м"):
        return timedelta(minutes=num)
    if unit in ("h", "ч"):
        return timedelta(hours=num)
    if unit in ("d", "д"):
        return timedelta(days=num)
    if unit in ("w", "н"):
        return timedelta(weeks=num)
    if unit in ("mon", "мес"):
        return timedelta(days=30 * num)
    if unit in ("y", "г"):
        return timedelta(days=365 * num)
    return None


def format_timedelta_remaining(until_dt: datetime) -> str:
    now = datetime.utcnow()
    diff = until_dt - now
    if diff.total_seconds() <= 0:
        return "закончено"
    seconds = int(diff.total_seconds())
    parts = []
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days:
        parts.append(f"{days}д")
    if hours:
        parts.append(f"{hours}ч")
    if minutes:
        parts.append(f"{minutes}м")
    if seconds and not parts:
        parts.append(f"{seconds}с")
    return " ".join(parts)