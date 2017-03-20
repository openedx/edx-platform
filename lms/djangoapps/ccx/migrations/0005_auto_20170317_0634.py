# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ccx', '0004_customcourseforedx_original_ccx_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customcourseforedx',
            name='original_ccx_id',
            field=models.IntegerField(null=True, verbose_name=b'ID of original CCX course entry', blank=True),
        ),
    ]
