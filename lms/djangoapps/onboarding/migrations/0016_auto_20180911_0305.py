# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0015_auto_20180809_0412'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluserextendedprofile',
            name='is_alquity_user',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userextendedprofile',
            name='is_alquity_user',
            field=models.BooleanField(default=False),
        ),
    ]
