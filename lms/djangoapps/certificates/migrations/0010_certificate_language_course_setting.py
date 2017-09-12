# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0008_schema__remove_badges'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificategenerationcoursesetting',
            name='can_use_language_specific_templates',
            field=models.BooleanField(default=False)
        ),
    ]
