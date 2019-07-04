# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0016_auto_20180911_0305'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluserextendedprofile',
            name='hear_about_philanthropy',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='historicaluserextendedprofile',
            name='hear_about_philanthropy_other',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userextendedprofile',
            name='hear_about_philanthropy',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userextendedprofile',
            name='hear_about_philanthropy_other',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
    ]
