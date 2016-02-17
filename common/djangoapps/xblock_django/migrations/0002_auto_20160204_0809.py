# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xblock_django', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='xblockdisableconfig',
            name='disabled_create_blocks',
            field=models.TextField(default=b'', help_text='Space-separated list of XBlock types whose creation to disable in Studio.', blank=True),
        ),
    ]
