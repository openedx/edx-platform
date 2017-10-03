# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0019_auto_20170920_0347'),
    ]

    operations = [
        migrations.RenameField(
            model_name='extendedprofile',
            old_name='are_surveys_complete',
            new_name='completed_survey',
        ),
        migrations.AlterField(
            model_name='extendedprofile',
            name='first_name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='extendedprofile',
            name='last_name',
            field=models.CharField(max_length=255),
        ),
    ]
