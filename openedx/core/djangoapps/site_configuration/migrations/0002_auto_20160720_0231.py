# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site_configuration', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='siteconfiguration',
            name='enabled',
            field=models.BooleanField(default=False, verbose_name=b'Enabled'),
        ),
        migrations.AddField(
            model_name='siteconfigurationhistory',
            name='enabled',
            field=models.BooleanField(default=False, verbose_name=b'Enabled'),
        ),
    ]
