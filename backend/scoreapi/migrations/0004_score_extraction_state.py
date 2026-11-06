from django.db import migrations, models


def recognize_existing_imports(apps, schema_editor):
    Score = apps.get_model("scoreapi", "Score")
    Passage = apps.get_model("scoreapi", "Passage")
    # Clear Score's multi-field default ordering and filter blank source files
    # in Python. Datastore otherwise translates exclude(source_file="") into
    # multiple inequality queries that require a composite index during a
    # fresh deployment.
    for score in Score.objects.all().order_by():
        if not score.source_file:
            continue
        suffix = score.source_file.name.rsplit(".", 1)[-1].lower()
        passages = list(Passage.objects.filter(score_id=score.pk).order_by())
        imported = suffix in {"musicxml", "xml", "mxl"} and bool(passages)
        # Earlier PDF OMR imports used Page N sections; a manual placeholder
        # alone must not be presented as successful extraction.
        imported = imported or (
            suffix == "pdf" and any(passage.section.startswith("Page ") for passage in passages)
        )
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
