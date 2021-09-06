# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0005_creditrequirement_sort_value'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='creditrequirement',
            options={'ordering': ['sort_value']},
        ),
    ]
