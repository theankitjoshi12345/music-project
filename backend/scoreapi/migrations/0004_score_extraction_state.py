from django.db import migrations, models


def recognize_existing_imports(apps, schema_editor):
    Score = apps.get_model("scoreapi", "Score")
    for score in Score.objects.exclude(source_file=""):
        suffix = score.source_file.name.rsplit(".", 1)[-1].lower()
        imported = suffix in {"musicxml", "xml", "mxl"} and score.passages.exists()
        # Earlier PDF OMR imports used Page N sections; a manual placeholder
        # alone must not be presented as successful extraction.
        imported = imported or (suffix == "pdf" and score.passages.filter(section__startswith="Page ").exists())
        if imported:
            score.extraction_state = "complete"
            score.save(update_fields=["extraction_state"])


class Migration(migrations.Migration):
    dependencies = [("scoreapi", "0003_score_source_file")]
    operations = [
        migrations.AddField(model_name="score", name="extraction_state", field=models.CharField(
            max_length=20, default="not_started", choices=[("not_started", "Not started"),
                ("processing", "Processing"), ("complete", "Complete"), ("failed", "Failed")])),
        migrations.AddField(model_name="score", name="extraction_error", field=models.CharField(max_length=500, blank=True)),
        migrations.AddField(model_name="score", name="extraction_updated_at", field=models.DateTimeField(null=True, blank=True)),
        migrations.RunPython(recognize_existing_imports, migrations.RunPython.noop),
    ]
