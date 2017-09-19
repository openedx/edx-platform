# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0003_auto_20170909_0408'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interestssurvey',
            name='reason_of_interest',
            field=models.CharField(max_length=256, blank=True),
        ),
    ]
