# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0014_courseoverview_certificate_available_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoverview',
            name='license',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
