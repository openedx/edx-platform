# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verify_student', '0003_auto_20151113_1443'),
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
