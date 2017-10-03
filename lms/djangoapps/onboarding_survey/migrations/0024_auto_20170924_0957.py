# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0023_auto_20170924_0951'),
    ]

    operations = [
        migrations.RenameField(
            model_name='history',
            old_name='total_annual_clients_or_beneficial',
            new_name='total_annual_clients_or_beneficiary',
        ),
    ]
