# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instructor_task', '0002_gradereportsetting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instructortask',
            name='task_input',
            field=models.CharField(max_length=512),
        ),
    ]
