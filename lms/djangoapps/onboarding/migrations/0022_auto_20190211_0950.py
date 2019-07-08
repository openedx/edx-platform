# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0021_auto_20190131_0434'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metricupdatepromptrecord',
            name='click',
            field=models.CharField(db_index=True, max_length=3, null=True, choices=[(b'RML', b'Remind Me Later'), (b'TMT', b'Take Me There'), (b'NT', b"No Thanks, I'm Not Interested")]),
        ),
    ]
