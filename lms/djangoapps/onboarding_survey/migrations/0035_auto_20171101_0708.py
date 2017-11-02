# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db import migrations, models


def reload_required_data(apps, user, defaults):


    try:
        data = json.loads(user.extended_profile.backup_user_data)
    except:
        # In case we were not able to populate the already
        # existing data due to partial signup, we will skip the step
        return

    role_in_org = apps.get_model("onboarding_survey", "RoleInsideOrg")
    user_info_survey_model = apps.get_model("onboarding_survey", "userinfosurvey")

    user_info_survey = user_info_survey_model.objects.get(user=user.id)
    user_info_survey.year_of_birth = data['date_of_birth_year']
    user_info_survey.start_month_year = data['start_month_year']

    if data['role_in_org']:
        user_info_survey.role_in_org = role_in_org.objects.get(pk=data['role_in_org'])

    if not user_info_survey.level_of_education:
        if defaults.get('level_of_education'):
            user_info_survey.level_of_education = defaults['level_of_education']

    if not user_info_survey.role_in_org:
        if defaults.get('role_inside_org'):
            user_info_survey.role_in_org = defaults['role_inside_org']

    user_info_survey.save()

    organization_survey_model = apps.get_model("onboarding_survey", "organizationsurvey")
    org_survey = organization_survey_model.objects.get(user=user.id)

    if not org_survey.total_employees:
        if defaults.get('total_employee'):
            org_survey.total_employees = defaults['total_employee']
            org_survey.save()


class Migration(migrations.Migration):
    def fix_broken_surveys(apps, schema_editor):
        user_model = apps.get_model("auth", "User")
        users = user_model.objects.exclude(username__in=['honor', 'edxapp', 'ecommerce_worker', 'verified', 'audit', 'user'])
        total_employee_model = apps.get_model("onboarding_survey", "TotalEmployee")
        education_level = apps.get_model("onboarding_survey", "EducationLevel")
        role_inside_org = apps.get_model("onboarding_survey", "RoleInsideOrg")

        defaults = {
            'total_employee': total_employee_model.objects.first(),
            'education_level': education_level.objects.first(),
            'role_inside_org': role_inside_org.objects.first(),
        }

        for user in users:
            reload_required_data(apps, user, defaults)

    dependencies = [
        ('onboarding_survey', '0033_auto_20171101_0602'),
    ]

    operations = [
        migrations.RunPython(fix_broken_surveys),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='level_of_education',
            field=models.ForeignKey(related_name='user_info_survey', default=1, to='onboarding_survey.EducationLevel'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='role_in_org',
            field=models.ForeignKey(related_name='user_info_survey', default=1, to='onboarding_survey.RoleInsideOrg'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='total_employees',
            field=models.ForeignKey(related_name='org_survey', default=1, to='onboarding_survey.TotalEmployee'),
            preserve_default=False,
        ),
    ]
