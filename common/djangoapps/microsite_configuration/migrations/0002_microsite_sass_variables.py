# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('microsite_configuration', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='microsite',
            name='sass_variables',
            field=models.TextField(blank=True),
        ),
    ]
