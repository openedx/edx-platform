# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0010_auto_20170207_0458'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseenrollmentallowed',
            name='mode',
            field=models.CharField(default=b'audit', max_length=100),
        ),
    ]
