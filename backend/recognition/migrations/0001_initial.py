from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RecognitionRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_filename", models.CharField(max_length=255)),
                ("upload_image_path", models.CharField(max_length=1024)),
                ("status", models.CharField(max_length=32)),
                ("plate_text", models.CharField(blank=True, max_length=64)),
                ("bbox", models.JSONField(blank=True, default=list)),
                ("yolo_confidence", models.FloatField(blank=True, null=True)),
                ("annotated_image_path", models.CharField(blank=True, max_length=1024)),
                ("crop_image_path", models.CharField(blank=True, max_length=1024)),
                ("raw_result", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        )
    ]
