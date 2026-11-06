"""Small, account-scoped traffic guard for the single Cloud Run instance.

Cloud Run and Firebase quotas remain the primary capacity boundary. These
throttles reject accidental loops and repeated expensive actions before they
reach Firestore, Cloud Storage, Poppler, or Audiveris.
"""

import hashlib

from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle


def _identity(request):
    ticket_owner = getattr(request, "extraction_owner", None) if request else None
    if ticket_owner:
        return ticket_owner
    subject = request.session.get("google_sub") if request else None
    if subject:
        return hashlib.sha256(subject.encode()).hexdigest()
    return None


class OwnerRateThrottle(SimpleRateThrottle):
    scope = "owner"

    def get_cache_key(self, request, view):
        identity = _identity(request)
        if identity:
            return self.cache_format % {"scope": self.scope, "ident": identity}
        # Public session/login/health requests have no Google subject yet.
        # DRF normalizes the client identifier and honors NUM_PROXIES when set.
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class OwnerScopedRateThrottle(ScopedRateThrottle):
    def get_cache_key(self, request, view):
        identity = _identity(request) or self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": identity}
