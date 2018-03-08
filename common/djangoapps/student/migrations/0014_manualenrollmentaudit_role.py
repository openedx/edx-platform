# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0013_delete_historical_enrollment_records'),
    ]

    operations = [
        migrations.AddField(
            model_name='manualenrollmentaudit',
            name='role',
            field=models.CharField(max_length=30, null=True, blank=True),
        ),
    ]
