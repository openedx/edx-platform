# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verify_student', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalverificationdeadline',
            name='deadline_is_explicit',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='verificationdeadline',
            name='deadline_is_explicit',
            field=models.BooleanField(default=True),
        ),
    ]
