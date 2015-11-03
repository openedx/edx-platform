# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0005_auto_20151208_0801'),
        ('badges', '0002_data__migrate_assertions'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='badgeassertion',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='badgeassertion',
            name='user',
        ),
        migrations.DeleteModel(
            name='BadgeImageConfiguration',
        ),
        migrations.DeleteModel(
            name='BadgeAssertion',
        ),
    ]
