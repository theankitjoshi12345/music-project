from rest_framework import serializers
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
            "measure_layout_version",
        ]

    def get_extraction_status(self, score):
        return "failed" if score.extraction_expired else score.extraction_state

    def get_extraction_error(self, score):
        if score.extraction_expired:
            return "The previous extraction was interrupted. Please retry."
        return score.extraction_error


class PassageSerializer(serializers.ModelSerializer):
    is_marked_for_practice = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = Passage
        fields = [
            "id",
            "section",
            "measure_number",
            "page_number",
            "is_marked_for_practice",
            "bounding_box",
            "preview_url",
        ]

    def get_preview_url(self, passage):
        if not passage.bounding_box:
            return None
        version = hashlib.sha256(json.dumps(passage.bounding_box, sort_keys=True).encode()).hexdigest()[:12]
        return f"/api/passages/{passage.id}/preview/?v={version}"

    def get_is_marked_for_practice(self, passage):
        request = self.context.get("request")
        owner = request.headers.get("X-Mock-User", "alex") if request else "alex"
        return passage.practice_marks.filter(owner=owner).exists()


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
