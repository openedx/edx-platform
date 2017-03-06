# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0007_certificateinvalidation'),
        ('badges', '0002_data__migrate_assertions'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BadgeImageConfiguration',
        ),
        migrations.DeleteModel(
            name='BadgeAssertion',
        ),
    ]
