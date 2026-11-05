from pathlib import Path
import subprocess
import secrets

from django.conf import settings
from django.db import IntegrityError
from django.http import FileResponse, HttpResponse
from django.db.models import Count
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Passage, PracticeMark, Score
from .extraction_service import ExtractionBusy, extract_score_measures
from .score_extract import OMRUnavailable, extract_musicxml_measures
from .serializers import PassageCreateSerializer, PassageSerializer, PracticeMarkSerializer, ScoreSerializer, ScoreUploadMetadataSerializer
from .upload_service import UploadQuotaExceeded, store_upload
from .pdf_render import render_pdf
from .pdf_safety import PDFSafetyError
from .access import is_demo, request_owner, score_owner, visible_scores


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Public liveness endpoint; it exposes no library or account details."""
    return Response({"status": "ok", "service": "score-companion-api"})


@api_view(["GET"])
@permission_classes([AllowAny])
def browser_session(request):
    if not is_demo() and not request.session.get("score_owner"):
        request.session.cycle_key()
        request.session["score_owner"] = secrets.token_hex(32)
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)
    response = Response({
        "auth_mode": settings.DJANGO_AUTH_MODE,
        "display_name": "Local practice profile" if is_demo() else "Private browser library",
        "csrfToken": get_token(request),
        "expires_in_seconds": None if is_demo() else settings.SESSION_COOKIE_AGE,
    })
    response["Cache-Control"] = "private, no-store"
    return response


class ScoreListView(APIView):
    def get(self, request):
        scores = visible_scores(request).annotate(passage_count=Count("passages"))
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
        metadata = ScoreUploadMetadataSerializer(data={
            "title": title, "movement": movement, "instrument": instrument,
            "page_count": max(page_count, extracted_page_count), "available_offline": True,
        })
        metadata.is_valid(raise_exception=True)
        try:
            score, created = store_upload(score_file, metadata.validated_data, extracted_measures, owner=score_owner(request))
        except UploadQuotaExceeded as error:
            return Response({"detail": str(error)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except IntegrityError:
            raise ValidationError({"score_file": "The score contains duplicate measure identifiers. Check the MusicXML file."})
        score = Score.objects.annotate(passage_count=Count("passages")).get(pk=score.pk)
        data = ScoreSerializer(score).data
        data["already_uploaded"] = not created
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ScoreDetailView(APIView):
    def get(self, request, score_id):
        score = get_object_or_404(
            visible_scores(request).annotate(passage_count=Count("passages")), pk=score_id
        )
        return Response(ScoreSerializer(score).data)

    def delete(self, request, score_id):
        score = get_object_or_404(visible_scores(request), pk=score_id)
        # Explicitly remove the uploaded file as well as its cascaded passages
        # and practice marks; Django does not delete FileField files by default.
        if score.source_file:
            score.source_file.delete(save=False)
        score.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(xframe_options_sameorigin, name="dispatch")
class ScoreFileView(APIView):
    def get(self, request, score_id):
        score = get_object_or_404(visible_scores(request), pk=score_id)
        if not score.source_file:
            return Response({"detail": "This score has no uploaded file."}, status=404)
        try:
            source = score.source_file.open("rb")
        except OSError:
            return Response({"detail": "This score file is unavailable."}, status=404)
        is_pdf = score.source_file.name.lower().endswith(".pdf")
        response = FileResponse(source, content_type="application/pdf" if is_pdf else "application/octet-stream",
                                as_attachment=not is_pdf, filename=Path(score.source_file.name).name)
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


class ScorePdfExtractionView(APIView):
    """Import PDF measures; duplicate requests retain saved IDs and marks."""

    def post(self, request, score_id):
        score = get_object_or_404(visible_scores(request), pk=score_id)
        if not score.source_file.name.lower().endswith(".pdf"):
            raise ValidationError({"score": "PDF measure extraction is only available for PDF scores."})
        try:
            extract_score_measures(score.pk)
        except ExtractionBusy as error:
            return Response({"detail": str(error)}, status=status.HTTP_409_CONFLICT)
        except Score.DoesNotExist:
            return Response({"detail": "That score was deleted."}, status=status.HTTP_404_NOT_FOUND)
        except OMRUnavailable as error:
            return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        score = Score.objects.annotate(passage_count=Count("passages")).get(pk=score.pk)
        return Response(ScoreSerializer(score).data)


class ScorePassageListView(APIView):
    def get(self, request, score_id):
        score = get_object_or_404(visible_scores(request), pk=score_id)
        passages = score.passages.prefetch_related("practice_marks")
        return Response(PassageSerializer(passages, many=True, context={"request": request}).data)

    def post(self, request, score_id):
        score = get_object_or_404(visible_scores(request), pk=score_id)
        serializer = PassageCreateSerializer(data=request.data, context={"score": score})
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        passage, created = Passage.objects.get_or_create(
            score=score, section=values["section"], measure_number=values["measure_number"],
            defaults={"page_number": values["page_number"]},
        )
        if passage.page_number != values["page_number"]:
            return Response({"detail": "That measure is already saved on a different page."}, status=status.HTTP_409_CONFLICT)
        return Response(PassageSerializer(passage, context={"request": request}).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ScorePageImageView(APIView):
    def get(self, request, score_id, page_number):
        score = get_object_or_404(visible_scores(request), pk=score_id)
        if not score.source_file.name.lower().endswith(".pdf") or not 1 <= page_number <= score.page_count:
            return Response({"detail": "That PDF page is not available."}, status=404)
        return pdf_image_response(score, page_number)


class PassagePreviewView(APIView):
    def get(self, request, passage_id):
        passage = get_object_or_404(Passage.objects.select_related("score").filter(score__in=visible_scores(request)), pk=passage_id)
        if not passage.bounding_box:
            return Response({"detail": "This measure has no saved position. Extract measure previews first."}, status=409)
        return pdf_image_response(passage.score, passage.page_number, passage.bounding_box)


def pdf_image_response(score, page_number, region=None):
    try:
        image = render_pdf(score.source_file.path, page_number, region)
    except PDFSafetyError as error:
        return Response({"detail": str(error)}, status=422)
    except (OSError, ValueError, subprocess.SubprocessError):
        return Response({"detail": "The score image could not be loaded. Check the PDF and retry."}, status=422)
    response = HttpResponse(image, content_type="image/png")
    response["Cache-Control"] = "private, max-age=300"
    return response


class PracticeMarkListCreateView(APIView):
    def get(self, request):
        owner = request_owner(request)
        marks = PracticeMark.objects.select_related("passage", "passage__score").prefetch_related("passage__practice_marks").filter(owner=owner, passage__score__in=visible_scores(request))
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
        values = serializer.validated_data
        mark, created = PracticeMark.objects.get_or_create(
            passage=values["passage"], owner=request_owner(request),
            defaults={key: value for key, value in values.items() if key != "passage"},
        )
        return Response(PracticeMarkSerializer(mark, context={"request": request}).data,
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class PracticeMarkDetailView(APIView):
    def delete(self, request, mark_id):
        owner = request_owner(request)
        mark = get_object_or_404(PracticeMark, pk=mark_id, owner=owner, passage__score__in=visible_scores(request))
        # Notes live on this row; no separate practice files or orphan notes remain.
        mark.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, mark_id):
        owner = request_owner(request)
        mark = get_object_or_404(PracticeMark, pk=mark_id, owner=owner, passage__score__in=visible_scores(request))
        serializer = PracticeMarkSerializer(mark, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        mark = serializer.save()
        return Response(PracticeMarkSerializer(mark, context={"request": request}).data)
