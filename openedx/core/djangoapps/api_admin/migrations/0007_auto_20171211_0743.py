# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_admin', '0006_catalog'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalapiaccessrequest',
            name='end_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='historicalapiaccessrequest',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalapiaccessrequest',
            name='start_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
