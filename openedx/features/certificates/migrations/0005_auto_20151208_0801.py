# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0004_certificategenerationhistory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generatedcertificate',
            name='verify_uuid',
            field=models.CharField(default=b'', max_length=32, db_index=True, blank=True),
        ),
    ]
