# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

# This migration is to add `on_delete=models.CASCADE` in `prompt` ( a FK in `metricupdatepromptrecord`)
# NOTE: This migration is created manually.


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0022_auto_20190211_0950'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metricupdatepromptrecord',
            name='prompt',
            field=models.ForeignKey(related_name='metrics_update_prompt_records', on_delete=models.CASCADE,
                                    to='onboarding.OrganizationMetricUpdatePrompt')
        ),
    ]
