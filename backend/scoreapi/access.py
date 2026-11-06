"""Server-owned anonymous sessions for the public course demonstration.

Demo profile headers are deliberately accepted only in explicit local demo mode.
An anonymous session is a browser identity, not a verified human account.
"""

import hashlib

from django.conf import settings
from django.core import signing
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Score


def is_demo():
    return settings.DJANGO_AUTH_MODE == "demo"


def request_owner(request):
    ticket_owner = getattr(request, "extraction_owner", None) if request else None
    if ticket_owner:
        return ticket_owner
    if is_demo():
        owner = request.headers.get("X-Mock-User", "alex") if request else "alex"
        if not owner or len(owner) > 64:
            raise PermissionDenied("Choose a valid local practice profile.")
        return owner
    if settings.DJANGO_AUTH_MODE == "google":
        subject = request.session.get("google_sub") if request else None
        owner = hashlib.sha256(subject.encode()).hexdigest() if subject else None
    else:
        owner = request.session.get("score_owner") if request else None
    if not owner:
        message = ("Sign in with Google to open your library." if settings.DJANGO_AUTH_MODE == "google"
                   else "Start a private browser session to open your library.")
        raise PermissionDenied(message)
    return owner


def score_owner(request):
    return None if is_demo() else request_owner(request)


def visible_scores(request):
    # Existing shared local scores remain NULL-owned and are never public.
    # Clear Meta.ordering: owner + title/movement/instrument would require a
    # composite Datastore index. Views sort the small, quota-limited result in
    # Python instead.
    return Score.objects.filter(owner=score_owner(request)).order_by()


class PrivateLibraryPermission(BasePermission):
    def has_permission(self, request, view):
        request_owner(request)
        if not is_demo() and request.method not in SAFE_METHODS:
            # DRF's default SessionAuthentication skips CSRF for anonymous users.
            # These anonymous sessions own real data, so enforce it explicitly.
            SessionAuthentication().enforce_csrf(request)
        return True


class ExtractionTicketPermission(BasePermission):
    """Accept a normal signed-in request or a narrowly scoped OMR ticket."""

    salt = "score-companion-extraction-v1"
    max_age = 15 * 60

    def has_permission(self, request, view):
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            try:
                payload = signing.loads(authorization[7:], salt=self.salt, max_age=self.max_age)
                score_id = int(view.kwargs.get("score_id"))
            except (signing.BadSignature, signing.SignatureExpired, TypeError, ValueError):
                return False
            owner = payload.get("owner")
            if not owner or len(owner) > 64 or payload.get("score_id") != score_id:
                return False
            request.extraction_owner = owner
            return True
        return PrivateLibraryPermission().has_permission(request, view)
