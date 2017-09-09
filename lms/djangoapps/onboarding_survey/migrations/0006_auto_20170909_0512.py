# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0005_auto_20170909_0443'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationsurvey',
            name='founding_year',
            field=models.PositiveSmallIntegerField(),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='total_annual_clients_or_beneficiary',
            field=models.PositiveIntegerField(),
        ),
    ]
