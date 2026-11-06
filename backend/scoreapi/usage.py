"""Persistent limits for expensive work that must survive cold starts."""

import hashlib

from django.conf import settings
from django.utils import timezone

from .models import UsageCounter


class UsageLimitExceeded(RuntimeError):
    pass


def consume_omr_allowance(owner):
    limit = settings.OMR_DAILY_LIMIT
    if limit < 1:
        raise UsageLimitExceeded("PDF recognition is temporarily unavailable to protect the service budget.")
    key = hashlib.sha256(f"{owner}:omr".encode()).hexdigest()
    today = timezone.localdate()
    try:
        counter = UsageCounter.objects.get(pk=key)
    except UsageCounter.DoesNotExist:
        counter = UsageCounter(key=key, owner=owner, action="omr", window_start=today, count=0)
    if counter.window_start != today:
        counter.window_start = today
        counter.count = 0
    if counter.count >= limit:
        raise UsageLimitExceeded(
            f"Daily PDF recognition limit reached ({limit}). Try again tomorrow or use MusicXML."
        )
    counter.count += 1
    counter.save()
