import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("scoreapi", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="practicemark",
            name="owner",
            field=models.CharField(default="alex", max_length=64),
        ),
        migrations.AlterField(
            model_name="practicemark",
            name="passage",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="practice_marks",
                to="scoreapi.passage",
            ),
        ),
        migrations.AddConstraint(
            model_name="practicemark",
            constraint=models.UniqueConstraint(
                fields=("passage", "owner"), name="unique_mark_per_passage_owner"
            ),
        ),
    ]
