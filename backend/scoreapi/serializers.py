from rest_framework import serializers

from .models import Passage, PracticeMark, Score


class ScoreSerializer(serializers.ModelSerializer):
    passage_count = serializers.IntegerField(read_only=True)
    extraction_status = serializers.SerializerMethodField()

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
        ]

    def get_extraction_status(self, score):
        extension = score.source_file.name.rsplit(".", 1)[-1].lower() if score.source_file else ""
        if extension == "pdf":
            return "manual_required"
        if extension in {"musicxml", "xml", "mxl"}:
            passage_count = getattr(score, "passage_count", None)
            if passage_count is None:
                passage_count = score.passages.count()
            return "extracted" if passage_count else "no_measures"
        return "manual_required"


class PassageSerializer(serializers.ModelSerializer):
    is_marked_for_practice = serializers.SerializerMethodField()

    class Meta:
        model = Passage
        fields = [
            "id",
            "section",
            "measure_number",
            "page_number",
            "is_marked_for_practice",
        ]

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
        if Passage.objects.filter(
            score=score,
            section=attrs["section"],
            measure_number=attrs["measure_number"],
        ).exists():
            raise serializers.ValidationError({"measure_number": "This section already has that measure."})
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
        if (
            self.instance is None
            and "passage" in attrs
            and PracticeMark.objects.filter(
                passage=attrs["passage"], owner=self.context["request"].headers.get("X-Mock-User", "alex")
            ).exists()
        ):
            raise serializers.ValidationError(
                {"passage_id": "This passage already has a practice mark."}
            )
        if self.instance is not None and "passage" in attrs:
            raise serializers.ValidationError(
                {"passage_id": "A practice mark cannot be moved to another passage."}
            )
        return attrs
