# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0008_auto_20161117_1209'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_poc',
            field=models.BooleanField(default=0),
        ),
    ]
