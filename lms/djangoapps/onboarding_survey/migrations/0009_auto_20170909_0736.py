# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('onboarding_survey', '0008_auto_20170909_0730'),
    ]

    operations = [
        migrations.AddField(
            model_name='interestssurvey',
            name='user',
            field=models.OneToOneField(related_name='interest_survey', null=True, blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='organizationsurvey',
            name='user',
            field=models.OneToOneField(related_name='organization_survey', null=True, blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='userinfosurvey',
            name='user',
            field=models.OneToOneField(related_name='user_info_survey', null=True, blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]
