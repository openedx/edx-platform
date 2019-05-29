# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import re

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_modes', '0009_suggested_prices_to_charfield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursemodesarchive',
            name='suggested_prices',
            field=models.CharField(default=b'', max_length=255, blank=True, validators=[django.core.validators.RegexValidator(re.compile('^[\\d,]+\\Z'), 'Enter only digits separated by commas.', 'invalid')]),
        ),
    ]
