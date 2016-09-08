# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import microsite_configuration.utils


class Migration(migrations.Migration):

    dependencies = [
        ('microsite_configuration', '0003_microsite_sass_variables'),
    ]

    operations = [
        migrations.AddField(
            model_name='microsite',
            name='page_elements',
            field=jsonfield.fields.JSONField(default=microsite_configuration.utils.get_initial_page_elements, blank=True),
        ),
        migrations.AlterField(
            model_name='microsite',
            name='sass_variables',
            field=models.TextField(default=microsite_configuration.utils.get_initial_sass_variables, blank=True),
        ),
    ]
