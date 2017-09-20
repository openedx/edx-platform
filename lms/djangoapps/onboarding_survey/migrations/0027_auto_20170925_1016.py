# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0026_auto_20170925_0938'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interestssurvey',
            name='reason_of_selected_interest',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='total_annual_revenue_for_last_fiscal_year',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
