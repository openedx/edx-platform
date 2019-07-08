# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0016_historicaluserprofile'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='historicaluserprofile',
            table='auth_historicaluserprofile',
        ),
    ]
