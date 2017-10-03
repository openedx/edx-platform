# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0028_auto_20170927_0747'),
    ]

    operations = [
        migrations.RenameField(
            model_name='extendedprofile',
            old_name='completed_survey',
            new_name='is_survey_completed',
        ),
        migrations.RenameField(
            model_name='organization',
            old_name='point_of_contact_exist',
            new_name='is_poc_exist',
        ),
        migrations.RemoveField(
            model_name='partnernetwork',
            name='network',
        ),
        migrations.AddField(
            model_name='partnernetwork',
            name='name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
