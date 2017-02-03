# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xblock_django', '0003_add_new_config_models'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='xblockdisableconfig',
            name='changed_by',
        ),
        migrations.DeleteModel(
            name='XBlockDisableConfig',
        ),
    ]
