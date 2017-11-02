# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db import migrations, models


def copy_required_data(apps, user):
    extended_profile_model = apps.get_model("onboarding_survey", "ExtendedProfile")

    try:
        extended_profile = extended_profile_model.objects.get(user=user.id)
        user_info_survey = user.user_info_survey
        organization_survey = user.organization_survey
    except:
        # In case we don't have data available, we dont have to create its
        # backup
        return

    data = {
        'date_of_birth_year': user_info_survey.dob.year if user_info_survey.dob else '1980',
        'start_month_year': organization_survey.start_month_year if organization_survey.start_month_year else '01/2017',
        'role_in_org': organization_survey.role_in_org.id if organization_survey.role_in_org else 1
    }

    extended_profile.backup_user_data = json.dumps(data)
    extended_profile.save()


class Migration(migrations.Migration):
    def fix_broken_surveys(apps, schema_editor):
        user_model = apps.get_model("auth", "User")
        users = user_model.objects.exclude(
            username__in=['honor', 'ecommerce_worker', 'verified', 'audit', 'user'])

        for user in users:
            copy_required_data(apps, user)

    dependencies = [
        ('onboarding_survey', '0031_auto_20171016_0846'),
    ]

    operations = [
        migrations.AddField(
            model_name='extendedprofile',
            name='backup_user_data',
            field=models.TextField(),
        ),
        migrations.RunPython(fix_broken_surveys)
    ]
