# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0010_auto_20170912_0323'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interestssurvey',
            name='personal_goal',
            field=models.ManyToManyField(to='onboarding_survey.PersonalGoal', blank=True),
        ),
    ]
