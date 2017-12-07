# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0014_auto_20170914_0817'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalcourseenrollment',
            name='end_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='historicalcourseenrollment',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalcourseenrollment',
            name='start_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
