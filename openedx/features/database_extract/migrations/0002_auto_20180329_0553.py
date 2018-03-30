# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database_extract', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='targetcourse',
            name='course_id',
            field=models.CharField(max_length=255),
        ),
    ]
