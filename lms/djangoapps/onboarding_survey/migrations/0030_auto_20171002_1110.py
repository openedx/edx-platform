# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0029_auto_20170927_1042'),
    ]

    operations = [
        migrations.RenameField(
            model_name='communitytypeinterest',
            old_name='community_type',
            new_name='label',
        ),
        migrations.RenameField(
            model_name='educationlevel',
            old_name='level',
            new_name='label',
        ),
        migrations.RenameField(
            model_name='englishproficiency',
            old_name='proficiency',
            new_name='label',
        ),
        migrations.RenameField(
            model_name='focusarea',
            old_name='area',
            new_name='label',
        ),
        migrations.RenameField(
            model_name='operationlevel',
            old_name='level',
            new_name='label',
        ),
        migrations.RenameField(
            model_name='organizationalcapacityarea',
            old_name='capacity_area',
            new_name='label',
        ),
        migrations.RenameField(
            model_name='orgsector',
            old_name='sector',
            new_name='label',
        ),
        migrations.RenameField(
            model_name='personalgoal',
            old_name='goal',
            new_name='label',
        ),
        migrations.RenameField(
            model_name='roleinsideorg',
            old_name='role',
            new_name='label',
        ),
        migrations.RenameField(
            model_name='totalemployee',
            old_name='total',
            new_name='label',
        ),
        migrations.RenameField(
            model_name='totalvolunteer',
            old_name='total',
            new_name='label',
        ),
    ]
