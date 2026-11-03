from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("scoreapi", "0005_score_content_sha256")]
    operations = [
        migrations.AddField(model_name="score", name="measure_layout_version", field=models.PositiveSmallIntegerField(default=0)),
        migrations.AddField(model_name="passage", name="bounding_box", field=models.JSONField(null=True, blank=True)),
    ]
