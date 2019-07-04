# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

# NOTE: name of migration starts with 004 kind of duplicate is because migration is being added
# by philu in ficus code, and now ironwood has it's own 004 but dates are different.

class Migration(migrations.Migration):

    dependencies = [
        ('verify_student', '0011_add_fields_to_sspv'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalverificationdeadline',
            name='end_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='historicalverificationdeadline',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalverificationdeadline',
            name='start_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
