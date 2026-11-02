from pathlib import Path

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


class ScoreUploadView(APIView):
    """Store an uploaded score in the local library with a usable starting passage."""

    allowed_extensions = {".pdf", ".musicxml", ".xml", ".mxl"}
    max_file_size = 10 * 1024 * 1024

    def post(self, request):
        score_file = request.FILES.get("score_file")
        if not score_file:
            raise ValidationError({"score_file": "Choose a score file to upload."})

        extension = Path(score_file.name).suffix.lower()
        if extension not in self.allowed_extensions:
            raise ValidationError({"score_file": "Upload a PDF, MusicXML, XML, or MXL score file."})
        if score_file.size > self.max_file_size:
            raise ValidationError({"score_file": "Score files must be 10 MB or smaller."})

        stem = Path(score_file.name).stem.replace("_", " ").strip() or "Untitled score"
        title = request.data.get("title", stem).strip() or stem
        movement = request.data.get("movement", stem).strip() or stem
        instrument = request.data.get("instrument", "Unassigned part").strip() or "Unassigned part"
        try:
            page_count = max(1, int(request.data.get("page_count", 1)))
        except (TypeError, ValueError):
            raise ValidationError({"page_count": "Enter a whole number of pages."})

        score = Score.objects.create(
            title=title,
            movement=movement,
            instrument=instrument,
            page_count=page_count,
            available_offline=True,
            source_file=score_file,
        )
        # Files are stored locally; detailed passage extraction is intentionally a
        # later concern. The first measure lets the uploaded part enter the same
        # practice workflow immediately.
        Passage.objects.create(score=score, section="Start", measure_number=1, page_number=1)
        score = Score.objects.annotate(passage_count=Count("passages")).get(pk=score.pk)
        return Response(ScoreSerializer(score, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ScoreDetailView(APIView):
    def get(self, request, score_id):
        score = get_object_or_404(
            Score.objects.annotate(passage_count=Count("passages")), pk=score_id
        )
        return Response(ScoreSerializer(score).data)


class ScorePassageListView(APIView):
    def get(self, request, score_id):
        score = get_object_or_404(Score, pk=score_id)
        passages = score.passages.prefetch_related("practice_marks")
        return Response(PassageSerializer(passages, many=True, context={"request": request}).data)


class PracticeMarkListCreateView(APIView):
    def get(self, request):
        owner = request.headers.get("X-Mock-User", "alex")
        marks = PracticeMark.objects.select_related("passage").filter(owner=owner)
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

        return Response(PracticeMarkSerializer(marks, many=True, context={"request": request}).data)

    def post(self, request):
        serializer = PracticeMarkSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        mark = serializer.save(owner=request.headers.get("X-Mock-User", "alex"))
        return Response(PracticeMarkSerializer(mark, context={"request": request}).data, status=status.HTTP_201_CREATED)


class PracticeMarkDetailView(APIView):
    def patch(self, request, mark_id):
        owner = request.headers.get("X-Mock-User", "alex")
        mark = get_object_or_404(PracticeMark, pk=mark_id, owner=owner)
        serializer = PracticeMarkSerializer(mark, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        mark = serializer.save()
        return Response(PracticeMarkSerializer(mark, context={"request": request}).data)
