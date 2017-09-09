# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0007_partnernetwork_is_partner_affiliated'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserInfoSurvey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dob', models.DateField()),
                ('language', models.CharField(max_length=256)),
                ('country_of_residence', models.CharField(max_length=256)),
                ('city_of_residence', models.CharField(max_length=256)),
                ('is_country_or_city_different', models.BooleanField(default=False)),
                ('country_of_employment', models.CharField(max_length=256, blank=True)),
                ('city_of_employment', models.CharField(max_length=256, blank=True)),
                ('english_prof', models.ForeignKey(related_name='user_info_survey', to='onboarding_survey.EnglishProficiency')),
                ('level_of_education', models.ForeignKey(related_name='user_info_survey', to='onboarding_survey.EducationLevel')),
            ],
        ),
        migrations.RemoveField(
            model_name='learnersurvey',
            name='english_prof',
        ),
        migrations.RemoveField(
            model_name='learnersurvey',
            name='level_of_education',
        ),
        migrations.DeleteModel(
            name='LearnerSurvey',
        ),
    ]
