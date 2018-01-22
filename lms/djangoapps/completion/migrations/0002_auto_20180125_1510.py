# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('completion', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blockcompletion',
            options={'get_latest_by': 'modified'},
        ),
    ]
