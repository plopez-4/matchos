"""Bounded, shared deployment cooldown. No automatic retries or provider-body logging."""
from collections import OrderedDict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math
import threading
import time

LOCK = threading.Lock()
COOLDOWNS = OrderedDict()


class CoolingDown(Exception):
    def __init__(self, seconds):
        self.seconds = seconds


def remaining(endpoint, deployment):
    now = time.monotonic()
    with LOCK:
        for key, deadline in list(COOLDOWNS.items()):
            if deadline <= now:
                COOLDOWNS.pop(key, None)
        return max(0, math.ceil(COOLDOWNS.get((endpoint.rstrip('/'), deployment), now)-now))


def require_ready(endpoint, deployment):
    seconds = remaining(endpoint, deployment)
    if seconds:
        raise CoolingDown(seconds)


def record_limit(endpoint, deployment, headers):
    waits = []
    for name, divisor in (('retry-after-ms',1000), ('retry-after',1)):
        raw = headers.get(name)
        if raw is None:
            continue
        try:
            delay = float(raw)/divisor
        except (ValueError,TypeError):
            try:
                stamp = parsedate_to_datetime(raw)
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=timezone.utc)
                delay = (stamp-datetime.now(timezone.utc)).total_seconds() if name=='retry-after' else -1
            except (ValueError,TypeError,OverflowError):
                continue
        if math.isfinite(delay) and delay >= 0:
            waits.append(delay)
    seconds = max(1, math.ceil(max(waits))) if waits else 60
    key = (endpoint.rstrip('/'), deployment)
    with LOCK:
        COOLDOWNS[key] = max(COOLDOWNS.get(key,0), time.monotonic()+seconds)
        COOLDOWNS.move_to_end(key)
        while len(COOLDOWNS)>8:
            COOLDOWNS.popitem(last=False)
    return remaining(endpoint, deployment)


def check_response(response, endpoint, deployment):
    if response.status_code==429:
        record_limit(endpoint, deployment, response.headers)
    response.raise_for_status()


def cacheable(result):
    """A transient capacity fallback must not poison this snapshot's cache."""
    reason = (result.get('fan_briefing') or {}).get('narrative',{}).get('fallback_reason')
    return reason not in ('provider_http_429','provider_cooldown')
