# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('verify_student', '0002_auto_20151124_1024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalverificationdeadline',
            name='deadline_is_explicit',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='verificationdeadline',
            name='deadline_is_explicit',
            field=models.BooleanField(default=False),
        ),
    ]
