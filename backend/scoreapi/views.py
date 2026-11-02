from pathlib import Path
import subprocess

from django.conf import settings
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Passage, PracticeMark, Score
from .score_extract import OMRUnavailable, extract_musicxml_measures, extract_pdf_measures
from .serializers import PassageCreateSerializer, PassageSerializer, PracticeMarkSerializer, ScoreSerializer


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

        try:
            extracted_measures = extract_musicxml_measures(score_file)
        except ValueError as error:
            raise ValidationError({"score_file": str(error)})
        extracted_page_count = max((page for _, _, page in extracted_measures), default=1)
        score = Score.objects.create(
            title=title,
            movement=movement,
            instrument=instrument,
            page_count=max(page_count, extracted_page_count),
            available_offline=True,
            source_file=score_file,
        )
        if extracted_measures:
            Passage.objects.bulk_create([
                Passage(score=score, section=section, measure_number=number, page_number=page)
                for section, number, page in extracted_measures
            ])
        score = Score.objects.annotate(passage_count=Count("passages")).get(pk=score.pk)
        return Response(ScoreSerializer(score, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ScoreDetailView(APIView):
    def get(self, request, score_id):
        score = get_object_or_404(
            Score.objects.annotate(passage_count=Count("passages")), pk=score_id
        )
        return Response(ScoreSerializer(score).data)

    def delete(self, request, score_id):
        score = get_object_or_404(Score, pk=score_id)
        # Explicitly remove the uploaded file as well as its cascaded passages
        # and practice marks; Django does not delete FileField files by default.
        if score.source_file:
            score.source_file.delete(save=False)
        score.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScorePdfExtractionView(APIView):
    """Replace a PDF score's passages with locally recognized OMR measures."""

    def post(self, request, score_id):
        score = get_object_or_404(Score, pk=score_id)
        if not score.source_file.name.lower().endswith(".pdf"):
            raise ValidationError({"score": "PDF measure extraction is only available for PDF scores."})
        try:
            measures = extract_pdf_measures(score.source_file.path, settings.AUDIVERIS_COMMAND)
        except OMRUnavailable as error:
            return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as error:
            return Response({"detail": f"Could not extract measures: {error}"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        score.passages.all().delete()
        Passage.objects.bulk_create([Passage(score=score, section=section, measure_number=number, page_number=page) for section, number, page in measures])
        score.page_count = max(page for _, _, page in measures)
        score.save(update_fields=["page_count"])
        score = Score.objects.annotate(passage_count=Count("passages")).get(pk=score.pk)
        return Response(ScoreSerializer(score).data)


class ScorePassageListView(APIView):
    def get(self, request, score_id):
        score = get_object_or_404(Score, pk=score_id)
        passages = score.passages.prefetch_related("practice_marks")
        return Response(PassageSerializer(passages, many=True, context={"request": request}).data)

    def post(self, request, score_id):
        score = get_object_or_404(Score, pk=score_id)
        serializer = PassageCreateSerializer(data=request.data, context={"score": score})
        serializer.is_valid(raise_exception=True)
        passage = serializer.save(score=score)
        return Response(PassageSerializer(passage, context={"request": request}).data, status=status.HTTP_201_CREATED)


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
