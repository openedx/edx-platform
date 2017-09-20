# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0022_auto_20170924_0941'),
    ]

    operations = [
        migrations.RenameField(
            model_name='organizationsurvey',
            old_name='start_mon_year',
            new_name='start_month_year',
        ),
    ]
