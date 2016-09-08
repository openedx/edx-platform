# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('microsite_configuration', '0002_auto_20160202_0228'),
    ]

    operations = [
        migrations.AddField(
            model_name='microsite',
            name='sass_variables',
            field=models.TextField(blank=True),
        ),
    ]
