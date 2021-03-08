from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoverview',
            name='announcement',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='catalog_visibility',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='course_video_url',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='effort',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='courseoverview',
            name='short_description',
            field=models.TextField(null=True),
        ),
    ]
