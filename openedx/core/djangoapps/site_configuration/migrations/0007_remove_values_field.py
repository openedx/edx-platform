# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('site_configuration', '0006_copy_values_to_site_values'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='siteconfiguration',
            name='values',
        ),
        migrations.RemoveField(
            model_name='siteconfigurationhistory',
            name='values',
        ),
    ]
