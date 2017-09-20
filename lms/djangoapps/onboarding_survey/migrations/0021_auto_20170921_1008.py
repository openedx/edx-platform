# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0020_auto_20170921_0753'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extendedprofile',
            name='org_admin_email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='extendedprofile',
            name='organization',
            field=models.ForeignKey(related_name='extended_profiles', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.Organization', null=True),
        ),
    ]
