# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0024_auto_20170924_0957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='history',
            name='end_data',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
