# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0012_courseoverview_eligible_for_financial_aid'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoverview',
            name='language',
            field=models.TextField(null=True),
        ),
    ]
