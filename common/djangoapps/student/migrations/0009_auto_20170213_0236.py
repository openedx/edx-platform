# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0008_auto_20170209_0821'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidateexpertise',
            name='rank',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='candidateprofile',
            name='extra_curricular_activities',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='candidateprofile',
            name='freelance_work',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
