# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0008_auto_20180207_0649'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='country',
            field=models.CharField(default='Invalid', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='currency',
            name='minor_units',
            field=models.CharField(default='Invalid', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='currency',
            name='number',
            field=models.CharField(default='Invalid', max_length=255),
            preserve_default=False,
        ),
    ]
