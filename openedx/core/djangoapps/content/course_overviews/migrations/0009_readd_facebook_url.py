# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0008_remove_courseoverview_facebook_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoverview',
            name='facebook_url',
            field=models.TextField(null=True),
        ),
    ]
