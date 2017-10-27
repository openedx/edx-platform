# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0016_auto_20170916_0845'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extendedprofile',
            name='is_poc',
            field=models.BooleanField(default=False, choices=[(True, b'Yes'), (False, b'No')]),
        ),
    ]
