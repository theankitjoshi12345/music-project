from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    """Temporary API health check for the P#9 application shell."""
    return Response({"status": "ok", "service": "score-companion-api"})
