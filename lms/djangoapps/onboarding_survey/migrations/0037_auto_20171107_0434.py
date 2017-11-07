# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0036_auto_20171102_1055'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='history',
            name='dob',
        ),
        migrations.RemoveField(
            model_name='history',
            name='goal_develop_leadership',
        ),
        migrations.RemoveField(
            model_name='history',
            name='is_currently_employed',
        ),
        migrations.RemoveField(
            model_name='history',
            name='org_capacity_administration',
        ),
        migrations.RemoveField(
            model_name='history',
            name='org_capacity_external_relation',
        ),
        migrations.RemoveField(
            model_name='history',
            name='org_capacity_finance',
        ),
        migrations.RemoveField(
            model_name='history',
            name='org_capacity_leadership',
        ),
        migrations.RemoveField(
            model_name='history',
            name='org_capacity_logistics',
        ),
        migrations.RemoveField(
            model_name='history',
            name='org_capacity_program',
        ),
        migrations.RemoveField(
            model_name='history',
            name='org_start_month_year',
        ),
        migrations.RemoveField(
            model_name='history',
            name='org_total_clients',
        ),
        migrations.RemoveField(
            model_name='history',
            name='org_total_revenue',
        ),
        migrations.RemoveField(
            model_name='history',
            name='org_total_volunteers',
        ),
        migrations.RemoveField(
            model_name='history',
            name='partner_network',
        ),
        migrations.RemoveField(
            model_name='history',
            name='reason_of_selected_interest',
        ),
        migrations.AddField(
            model_name='history',
            name='can_provide_info',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='history',
            name='coi_diff_from_me',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='currency',
            field=models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.Currency', null=True),
        ),
        migrations.AddField(
            model_name='history',
            name='info_accuracy',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='history',
            name='last_fiscal_year_end_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='history',
            name='org_alternate_admin_email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='history',
            name='org_eff_engagement_and_partnership',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='org_eff_financial_management',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='org_eff_fundraising_and_mobilization',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='org_eff_human_resource',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='org_eff_leadership_and_gov',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='org_eff_marketing_and_PR',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='org_eff_measurement_and_learning',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='org_eff_program_design_and_dev',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='org_eff_strategy_and_planning',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='org_eff_system_and_process',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='org_is_url_exist',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='history',
            name='partner_network_acumen',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='partner_network_fhi_360',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='partner_network_global_giving',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='partner_network_mercy_corps',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='start_month_year',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='history',
            name='total_clients',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='history',
            name='total_employees',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='history',
            name='total_expenses',
            field=models.BigIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='history',
            name='total_program_expenses',
            field=models.BigIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='history',
            name='total_revenue',
            field=models.BigIntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='history',
            name='user_fn_engagement_and_partnership',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='user_fn_financial_management',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='user_fn_fundraising_and_mobilization',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='user_fn_human_resource',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='user_fn_leadership_and_gov',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='user_fn_marketing_and_PR',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='user_fn_measurement_and_learning',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='user_fn_program_design_and_dev',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='user_fn_strategy_and_planning',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='user_fn_system_and_process',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='history',
            name='weekly_work_hours',
            field=models.PositiveIntegerField(default=0, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='history',
            name='year_of_birth',
            field=models.PositiveIntegerField(default=1920, blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='total_employees',
            field=models.ForeignKey(related_name='org_survey', to='onboarding_survey.TotalEmployee', null=True),
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='level_of_education',
            field=models.ForeignKey(related_name='user_info_survey', to='onboarding_survey.EducationLevel', null=True),
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='role_in_org',
            field=models.ForeignKey(related_name='user_info_survey', to='onboarding_survey.RoleInsideOrg', null=True),
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='year_of_birth',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1900, message=b'Ensure year of birth is greater than or equal to 1900'), django.core.validators.MaxValueValidator(2017, message=b'Ensure year of birth is less than or equal to 2017')]),
        ),
    ]
