# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instructor_task', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instructortask',
            name='task_input',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='instructortask',
            name='task_output',
            field=models.TextField(null=True),
        ),
    ]
