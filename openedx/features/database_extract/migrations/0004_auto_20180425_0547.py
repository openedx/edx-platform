# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database_extract', '0003_targetcourse_email_list'),
    ]

    operations = [
        migrations.RenameField(
            model_name='targetcourse',
            old_name='email_list',
            new_name='emails',
        ),
    ]
