# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0027_auto_20170925_1016'),
    ]

    operations = [
        migrations.RenameField(
            model_name='history',
            old_name='community_of_interest_learner_from_my_region',
            new_name='coi_same_region',
        ),
        migrations.RenameField(
            model_name='history',
            old_name='community_of_interest_learner_for_similar_org',
            new_name='coi_similar_org',
        ),
        migrations.RenameField(
            model_name='history',
            old_name='community_of_interest_learner_interested_in_similar_org_capacity',
            new_name='coi_similar_org_capacity',
        ),
        migrations.RenameField(
            model_name='history',
            old_name='personal_goal_contribute_to_organization',
            new_name='goal_contribute_to_org',
        ),
        migrations.RenameField(
            model_name='history',
            old_name='personal_goal_develop_leadership',
            new_name='goal_develop_leadership',
        ),
        migrations.RenameField(
            model_name='history',
            old_name='personal_goal_gain_new_skill',
            new_name='goal_gain_new_skill',
        ),
        migrations.RenameField(
            model_name='history',
            old_name='personal_goal_improve_job_prospect',
            new_name='goal_improve_job_prospect',
        ),
        migrations.RenameField(
            model_name='history',
            old_name='personal_goal_build_relation_with_other',
            new_name='goal_relation_with_other',
        ),
        migrations.RenameField(
            model_name='history',
            old_name='is_employment_location_different',
            new_name='is_emp_location_different',
        ),
        migrations.RenameField(
            model_name='history',
            old_name='org_total_annual_clients_or_beneficiary',
            new_name='org_total_clients',
        ),
        migrations.RenameField(
            model_name='history',
            old_name='org_total_annual_revenue_for_last_fiscal_year',
            new_name='org_total_revenue',
        ),
        migrations.RenameField(
            model_name='organizationsurvey',
            old_name='total_annual_clients_or_beneficiary',
            new_name='total_clients',
        ),
        migrations.RenameField(
            model_name='organizationsurvey',
            old_name='total_annual_revenue_for_last_fiscal_year',
            new_name='total_revenue',
        ),
        migrations.RenameField(
            model_name='userinfosurvey',
            old_name='is_employment_location_different',
            new_name='is_emp_location_different',
        ),
    ]
