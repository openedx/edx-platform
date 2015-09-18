# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creditrequirementstatus',
            name='status',
            field=models.CharField(max_length=32, choices=[(b'satisfied', b'satisfied'), (b'failed', b'failed'), (b'declined', b'declined')]),
        ),
        migrations.AlterField(
            model_name='historicalcreditrequirementstatus',
            name='status',
            field=models.CharField(max_length=32, choices=[(b'satisfied', b'satisfied'), (b'failed', b'failed'), (b'declined', b'declined')]),
        ),
    ]
