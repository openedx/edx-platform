# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0014_auto_20170915_1021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extendedprofile',
            name='is_poc',
            field=models.BooleanField(default=0, choices=[(True, b'Yes'), (False, b'No')]),
        ),
    ]
