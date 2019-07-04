# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oef', '0010_load_instructions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oefsurvey',
            name='description',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='topicquestion',
            name='score_name',
            field=models.CharField(max_length=50),
        ),
    ]
