# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0002_auto_20170908_0751'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interestssurvey',
            name='inclusion_in_community',
        ),
        migrations.AddField(
            model_name='interestssurvey',
            name='reason_of_interest',
            field=models.CharField(default='not_provided', max_length=256),
            preserve_default=False,
        ),
    ]
