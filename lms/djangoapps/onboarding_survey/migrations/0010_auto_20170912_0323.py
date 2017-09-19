# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0009_auto_20170909_0736'),
    ]

    operations = [
        migrations.DeleteModel(
            name='InclusionInCommunityChoice',
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='city_of_residence',
            field=models.CharField(max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='dob',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='level_of_education',
            field=models.ForeignKey(related_name='user_info_survey', blank=True, to='onboarding_survey.EducationLevel', null=True),
        ),
    ]
