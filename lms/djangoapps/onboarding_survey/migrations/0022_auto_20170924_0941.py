# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('onboarding_survey', '0021_auto_20170921_1008'),
    ]

    operations = [
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('community_learner_for_similar_org', models.BooleanField(default=False)),
                ('community_learner_interested_in_similar_org_capacity', models.BooleanField(default=False)),
                ('community_learner_from_my_region', models.BooleanField(default=False)),
                ('logistics', models.BooleanField(default=False)),
                ('administration', models.BooleanField(default=False)),
                ('finance', models.BooleanField(default=False)),
                ('external_relation', models.BooleanField(default=False)),
                ('program', models.BooleanField(default=False)),
                ('leadership', models.BooleanField(default=False)),
                ('gain_new_skill', models.BooleanField(default=False)),
                ('build_relation_with_other', models.BooleanField(default=False)),
                ('develop_leadership', models.BooleanField(default=False)),
                ('improve_job_prospect', models.BooleanField(default=False)),
                ('contribute_to_organization', models.BooleanField(default=False)),
                ('dob', models.DateField(null=True, blank=True)),
                ('language', models.CharField(max_length=255)),
                ('country_of_residence', models.CharField(max_length=255)),
                ('city_of_residence', models.CharField(max_length=255, blank=True)),
                ('is_country_or_city_different', models.BooleanField(default=False)),
                ('country_of_employment', models.CharField(max_length=255, blank=True)),
                ('city_of_employment', models.CharField(max_length=255, blank=True)),
                ('reason_of_interest', models.CharField(max_length=255, blank=True)),
                ('start_month_year', models.CharField(max_length=100, blank=True)),
                ('country', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255, blank=True)),
                ('url', models.URLField(max_length=255, blank=True)),
                ('founding_year', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('total_annual_clients_or_beneficial', models.PositiveIntegerField(null=True, blank=True)),
                ('total_annual_revenue_for_last_fiscal', models.CharField(max_length=255, blank=True)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('is_poc', models.BooleanField(default=False, choices=[(0, b'No'), (1, b'Yes')])),
                ('is_currently_employed', models.BooleanField(default=False)),
                ('org_admin_email', models.EmailField(max_length=254, null=True, blank=True)),
                ('start_data', models.DateTimeField(auto_now_add=True)),
                ('end_data', models.DateTimeField(auto_now=True, null=True)),
                ('english_prof', models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.EnglishProficiency', null=True)),
                ('focus_area', models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.FocusArea', null=True)),
                ('level_of_education', models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.EducationLevel', null=True)),
                ('level_of_op', models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.OperationLevel', null=True)),
                ('organization', models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.Organization', null=True)),
                ('partner_network', models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.PartnerNetwork', null=True)),
                ('role_in_org', models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.RoleInsideOrg', null=True)),
                ('sector', models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.OrgSector', null=True)),
                ('total_employees', models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.TotalEmployee', null=True)),
                ('total_volunteers', models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.TotalVolunteer', null=True)),
                ('user', models.ForeignKey(related_name='user_history', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.RenameField(
            model_name='organizationsurvey',
            old_name='state_mon_year',
            new_name='start_mon_year',
        ),
        migrations.AlterField(
            model_name='extendedprofile',
            name='is_poc',
            field=models.BooleanField(default=False, choices=[(0, b'No'), (1, b'Yes')]),
        ),
    ]
