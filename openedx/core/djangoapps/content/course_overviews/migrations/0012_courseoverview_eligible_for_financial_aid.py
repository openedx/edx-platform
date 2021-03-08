from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0011_courseoverview_marketing_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoverview',
            name='eligible_for_financial_aid',
            field=models.BooleanField(default=True),
        ),
    ]
