# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('microsite_configuration', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='micrositehistory',
            name='key',
            field=models.CharField(max_length=63, db_index=True),
        ),
        migrations.AlterField(
            model_name='micrositehistory',
            name='site',
            field=models.ForeignKey(related_name='microsite_history', to='sites.Site'),
        ),
    ]
