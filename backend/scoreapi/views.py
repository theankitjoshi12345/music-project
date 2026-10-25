from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Passage, PracticeMark, Score
from .serializers import PassageSerializer, PracticeMarkSerializer, ScoreSerializer


@api_view(["GET"])
def health_check(request):
    """Temporary API health check for the P#9 application shell."""
    return Response({"status": "ok", "service": "score-companion-api"})


class ScoreListView(APIView):
    def get(self, request):
        scores = Score.objects.annotate(passage_count=Count("passages"))
        return Response(ScoreSerializer(scores, many=True).data)


class ScoreDetailView(APIView):
    def get(self, request, score_id):
        score = get_object_or_404(
            Score.objects.annotate(passage_count=Count("passages")), pk=score_id
        )
        return Response(ScoreSerializer(score).data)


class ScorePassageListView(APIView):
    def get(self, request, score_id):
        score = get_object_or_404(Score, pk=score_id)
        passages = score.passages.select_related("practice_mark")
        return Response(PassageSerializer(passages, many=True).data)


class PracticeMarkListCreateView(APIView):
    def get(self, request):
        marks = PracticeMark.objects.select_related("passage").all()
        score_id = request.query_params.get("score")
        mark_status = request.query_params.get("status")

        if score_id:
            marks = marks.filter(passage__score_id=score_id)
        if mark_status == "unresolved":
            marks = marks.filter(is_resolved=False)
        elif mark_status == "resolved":
            marks = marks.filter(is_resolved=True)
        elif mark_status:
            raise ValidationError({"status": "Use 'unresolved' or 'resolved'."})

        return Response(PracticeMarkSerializer(marks, many=True).data)

    def post(self, request):
        serializer = PracticeMarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mark = serializer.save()
        return Response(PracticeMarkSerializer(mark).data, status=status.HTTP_201_CREATED)


class PracticeMarkDetailView(APIView):
    def patch(self, request, mark_id):
        mark = get_object_or_404(PracticeMark, pk=mark_id)
        serializer = PracticeMarkSerializer(mark, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        mark = serializer.save()
        return Response(PracticeMarkSerializer(mark).data)
