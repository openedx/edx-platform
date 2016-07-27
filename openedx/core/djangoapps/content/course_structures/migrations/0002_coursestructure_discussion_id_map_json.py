# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import util.models


class Migration(migrations.Migration):

    dependencies = [
        ('course_structures', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursestructure',
            name='discussion_id_map_json',
            field=util.models.CompressedTextField(null=True, verbose_name=b'Discussion ID Map JSON', blank=True),
        ),
    ]
