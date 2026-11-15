# Generated manually so this migration also works with the Firestore backend.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("scoreapi", "0010_usagecounter")]

    operations = [
        migrations.CreateModel(
            name="LocalAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(max_length=64, unique=True)),
                ("password_hash", models.CharField(max_length=256)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["username"]},
        ),
    ]
