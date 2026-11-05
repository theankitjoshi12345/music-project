"""Server-owned anonymous sessions for the public course demonstration.

Demo profile headers are deliberately accepted only in explicit local demo mode.
An anonymous session is a browser identity, not a verified human account.
"""

from django.conf import settings
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Score


def is_demo():
    return settings.DJANGO_AUTH_MODE == "demo"


def request_owner(request):
    if is_demo():
        owner = request.headers.get("X-Mock-User", "alex") if request else "alex"
        if not owner or len(owner) > 64:
            raise PermissionDenied("Choose a valid local practice profile.")
        return owner
    owner = request.session.get("score_owner") if request else None
    if not owner:
        raise PermissionDenied("Start a private browser session to open your library.")
    return owner


def score_owner(request):
    return None if is_demo() else request_owner(request)


def visible_scores(request):
    # Existing shared local scores remain NULL-owned and are never public.
    return Score.objects.filter(owner=score_owner(request))


class PrivateLibraryPermission(BasePermission):
    def has_permission(self, request, view):
        request_owner(request)
        if not is_demo() and request.method not in SAFE_METHODS:
            # DRF's default SessionAuthentication skips CSRF for anonymous users.
            # These anonymous sessions own real data, so enforce it explicitly.
            SessionAuthentication().enforce_csrf(request)
        return True
