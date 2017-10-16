# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0011_certificatetemplate_alter_unique'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='certificategenerationcoursesetting',
            name='enabled',
        ),
    ]
