# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0011_auto_20180220_1229'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluserextendedprofile',
            name='is_first_learner',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userextendedprofile',
            name='is_first_learner',
            field=models.BooleanField(default=False),
        ),
    ]
