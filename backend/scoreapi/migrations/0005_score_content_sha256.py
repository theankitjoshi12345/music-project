from django.db import migrations, models
import scoreapi.models


class Migration(migrations.Migration):
    dependencies = [("scoreapi", "0004_score_extraction_state")]
    operations = [
        migrations.AddField(model_name="score", name="content_sha256", field=models.CharField(
            max_length=64, null=True, blank=True, unique=True, editable=False)),
        migrations.AlterField(model_name="score", name="source_file", field=models.FileField(
            upload_to=scoreapi.models.score_upload_path, blank=True)),
    ]
