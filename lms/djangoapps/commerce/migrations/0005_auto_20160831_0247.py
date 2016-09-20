# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('commerce', '0004_auto_20160531_0950'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commerceconfiguration',
            name='receipt_page',
        ),
        migrations.AddField(
            model_name='commerceconfiguration',
            name='site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='sites.Site', null=True),
        ),
    ]
