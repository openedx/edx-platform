# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learnersurvey',
            name='city_of_employment',
            field=models.CharField(max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='learnersurvey',
            name='country_of_employment',
            field=models.CharField(max_length=256, blank=True),
        ),
    ]
