# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0005_auto_20151208_0801'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificatetemplateasset',
            name='asset_slug',
            field=models.SlugField(help_text="Asset's unique slug. We can reference the asset in templates using this value.", max_length=255, unique=True, null=True),
        ),
    ]
