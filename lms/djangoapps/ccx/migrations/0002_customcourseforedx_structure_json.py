# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ccx', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customcourseforedx',
            name='structure_json',
            field=models.TextField(null=True, verbose_name=b'Structure JSON', blank=True),
        ),
    ]
