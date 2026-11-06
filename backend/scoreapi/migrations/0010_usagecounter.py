# Generated for persistent production cost limits.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("scoreapi", "0009_firestore_compatibility")]

    operations = [
        migrations.CreateModel(
            name="UsageCounter",
            fields=[
                ("key", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("owner", models.CharField(editable=False, max_length=64)),
                ("action", models.CharField(editable=False, max_length=32)),
                ("window_start", models.DateField()),
                ("count", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(fields=("owner", "action"), name="unique_usage_counter_action"),
                ],
            },
        ),
    ]
