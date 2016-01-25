# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0007_courseoverviewimageconfig'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='courseoverview',
            name='facebook_url',
        ),
    ]
