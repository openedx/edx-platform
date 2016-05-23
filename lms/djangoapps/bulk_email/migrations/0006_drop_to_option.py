# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulk_email', '0005_move_target_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='courseemail',
            name='to_option',
        ),
    ]
