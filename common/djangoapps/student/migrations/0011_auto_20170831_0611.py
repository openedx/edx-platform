# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0010_organization_point_of_contact_exist'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='point_of_contact_exist',
            field=models.BooleanField(default=False),
        ),
    ]
