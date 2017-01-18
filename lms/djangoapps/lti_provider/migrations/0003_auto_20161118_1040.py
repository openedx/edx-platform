# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import openedx.core.djangolib.fields


class Migration(migrations.Migration):

    dependencies = [
        ('lti_provider', '0002_auto_20160325_0407'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lticonsumer',
            name='instance_guid',
            field=openedx.core.djangolib.fields.CharNullField(max_length=255, unique=True, null=True, blank=True),
        ),
    ]
