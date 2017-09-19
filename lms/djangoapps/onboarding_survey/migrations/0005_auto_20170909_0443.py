# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0004_auto_20170909_0420'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationsurvey',
            name='founding_year',
            field=models.IntegerField(max_length=4),
        ),
    ]
