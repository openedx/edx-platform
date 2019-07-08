# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_card', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='coursecard',
            old_name='organization_domain',
            new_name='course_name',
        ),
    ]
