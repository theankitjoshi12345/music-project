from rest_framework import serializers

from .models import Passage, PracticeMark, Score


class ScoreSerializer(serializers.ModelSerializer):
    passage_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Score
        fields = [
            "id",
            "title",
            "movement",
            "instrument",
            "page_count",
            "available_offline",
            "passage_count",
        ]


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
        return hasattr(passage, "practice_mark")


class PracticeMarkSerializer(serializers.ModelSerializer):
    passage_id = serializers.PrimaryKeyRelatedField(
        source="passage",
        queryset=Passage.objects.all(),
        write_only=True,
        required=False,
    )
    passage = PassageSerializer(read_only=True)

    class Meta:
        model = PracticeMark
        fields = [
            "id",
            "passage",
            "passage_id",
            "note",
            "is_resolved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "passage", "created_at", "updated_at"]

    def validate_note(self, value):
        return value.strip()

    def validate(self, attrs):
        if self.instance is None and "passage" not in attrs:
            raise serializers.ValidationError({"passage_id": "This field is required."})
        if (
            self.instance is None
            and "passage" in attrs
            and PracticeMark.objects.filter(passage=attrs["passage"]).exists()
        ):
            raise serializers.ValidationError(
                {"passage_id": "This passage already has a practice mark."}
            )
        if self.instance is not None and "passage" in attrs:
            raise serializers.ValidationError(
                {"passage_id": "A practice mark cannot be moved to another passage."}
            )
        return attrs
