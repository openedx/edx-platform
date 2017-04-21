# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0005_commerceconfiguration_enable_automatic_refund_approval'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commerceconfiguration',
            name='receipt_page',
        ),
    ]
