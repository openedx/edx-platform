# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import openedx.core.djangoapps.appsembler.sites.utils


class Migration(migrations.Migration):

    dependencies = [
        ('site_configuration', '0003_add_sass_vars_and_page_elements'),
    ]

    operations = [
        migrations.AlterField(
            model_name='siteconfiguration',
            name='sass_variables',
            field=jsonfield.fields.JSONField(default=openedx.core.djangoapps.appsembler.sites.utils.get_initial_sass_variables, blank=True),
        ),
    ]
