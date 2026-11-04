from rest_framework import serializers
from django.conf import settings
import hashlib
import json

from .models import Passage, PracticeMark, Score


class ScoreUploadMetadataSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    movement = serializers.CharField(max_length=120)
    instrument = serializers.CharField(max_length=120)
    page_count = serializers.IntegerField(min_value=1)
    available_offline = serializers.BooleanField(default=True)


class ScoreSerializer(serializers.ModelSerializer):
    passage_count = serializers.IntegerField(read_only=True)
    extraction_status = serializers.SerializerMethodField()
    extraction_error = serializers.SerializerMethodField()
    extraction_started_at = serializers.SerializerMethodField()
    extraction_estimated_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Score
        fields = [
            "id",
            "title",
            "movement",
            "instrument",
            "page_count",
            "available_offline",
            "source_file",
            "passage_count",
            "extraction_status",
            "extraction_error",
            "extraction_started_at",
            "extraction_estimated_seconds",
            "measure_layout_version",
        ]

    def get_extraction_status(self, score):
        return "failed" if score.extraction_expired else score.extraction_state

    def get_extraction_error(self, score):
        if score.extraction_expired:
            return "The previous extraction was interrupted. Please retry."
        return score.extraction_error

    def get_extraction_started_at(self, score):
        if score.extraction_state == "processing" and not score.extraction_expired:
            return score.extraction_updated_at.isoformat()
        return None

    def get_extraction_estimated_seconds(self, score):
        if not score.source_file.name.lower().endswith(".pdf"):
            return None
        # Planning estimate, not a measurement of Audiveris's progress.
        return min(settings.OMR_TIMEOUT_SECONDS,
                   15 + score.page_count * settings.OMR_ESTIMATED_SECONDS_PER_PAGE)


class PassageSerializer(serializers.ModelSerializer):
    is_marked_for_practice = serializers.SerializerMethodField()
    practice_mark_id = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = Passage
        fields = [
            "id",
            "section",
            "measure_number",
            "page_number",
            "is_marked_for_practice",
            "practice_mark_id",
            "bounding_box",
            "preview_url",
        ]

    def get_preview_url(self, passage):
        if not passage.bounding_box:
            return None
        version = hashlib.sha256(json.dumps(passage.bounding_box, sort_keys=True).encode()).hexdigest()[:12]
        return f"/api/passages/{passage.id}/preview/?v={version}"

    def get_is_marked_for_practice(self, passage):
        return self.get_practice_mark_id(passage) is not None

    def get_practice_mark_id(self, passage):
        request = self.context.get("request")
        owner = request.headers.get("X-Mock-User", "alex") if request else "alex"
        return next((mark.id for mark in passage.practice_marks.all() if mark.owner == owner), None)


class PassageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passage
        fields = ["id", "section", "measure_number", "page_number"]

    def validate_section(self, value):
        return value.strip() or "Start"

    def validate(self, attrs):
        score = self.context["score"]
        if attrs["page_number"] < 1 or attrs["page_number"] > score.page_count:
            raise serializers.ValidationError({"page_number": "Choose an existing page in this score."})
        if attrs["measure_number"] < 1:
            raise serializers.ValidationError({"measure_number": "Measure numbers start at one."})
        return attrs


class PracticeMarkPassageSerializer(PassageSerializer):
    movement = serializers.CharField(source="score.movement", read_only=True)
    score_id = serializers.IntegerField(read_only=True)

    class Meta(PassageSerializer.Meta):
        fields = PassageSerializer.Meta.fields + ["movement", "score_id"]


class PracticeMarkSerializer(serializers.ModelSerializer):
    passage_id = serializers.PrimaryKeyRelatedField(
        source="passage",
        queryset=Passage.objects.all(),
        write_only=True,
        required=False,
    )
    passage = PracticeMarkPassageSerializer(read_only=True)

    class Meta:
        model = PracticeMark
        fields = [
            "id",
            "owner",
            "passage",
            "passage_id",
            "note",
            "is_resolved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "passage", "created_at", "updated_at"]
        validators = []

    def validate_note(self, value):
        return value.strip()

    def validate(self, attrs):
        if self.instance is None and "passage" not in attrs:
            raise serializers.ValidationError({"passage_id": "This field is required."})
        if self.instance is not None and "passage" in attrs:
            raise serializers.ValidationError(
                {"passage_id": "A practice mark cannot be moved to another passage."}
            )
        return attrs
