# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('api_admin', '0003_auto_20160404_1618'),
    ]

    operations = [
        migrations.AddField(
            model_name='apiaccessrequest',
            name='contacted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='apiaccessrequest',
            name='site',
            field=models.ForeignKey(default=1, to='sites.Site'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicalapiaccessrequest',
            name='contacted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalapiaccessrequest',
            name='site',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='sites.Site', null=True),
        ),
    ]
