# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0007_auto_20180131_0527'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicaluserextendedprofile',
            name='level_of_education',
            field=models.CharField(max_length=270, null=True, blank=True),
        ),
    ]
