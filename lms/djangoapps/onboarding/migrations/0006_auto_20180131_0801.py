# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0005_auto_20180118_0657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicaluserextendedprofile',
            name='level_of_education',
            field=models.CharField(max_length=270, null=True, blank=True),
        ),
    ]
