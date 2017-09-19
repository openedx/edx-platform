# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CommunityTypeInterest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('community_type', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='EducationLevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('level', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='EnglishProficiency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('proficiency', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='FocusArea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('area', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='InclusionInCommunityChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('choice', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='InterestsSurvey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='LearnerSurvey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dob', models.DateField()),
                ('language', models.CharField(max_length=256)),
                ('country_of_residence', models.CharField(max_length=256)),
                ('city_of_residence', models.CharField(max_length=256)),
                ('is_country_or_city_different', models.BooleanField(default=False)),
                ('country_of_employment', models.CharField(max_length=256)),
                ('city_of_employment', models.CharField(max_length=256)),
                ('english_prof', models.ForeignKey(related_name='learner_survey', to='onboarding_survey.EnglishProficiency')),
                ('level_of_education', models.ForeignKey(related_name='learner_survey', to='onboarding_survey.EducationLevel')),
            ],
        ),
        migrations.CreateModel(
            name='OperationLevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('level', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='OrganizationalCapacityArea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('capacity_area', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='OrganizationSurvey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state_mon_year', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=256)),
                ('city', models.CharField(max_length=265)),
                ('url', models.URLField(max_length=256)),
                ('founding_year', models.CharField(max_length=10)),
                ('total_annual_clients_or_beneficiary', models.CharField(max_length=256)),
                ('total_annual_revenue_for_last_fiscal', models.CharField(max_length=256)),
                ('focus_area', models.ForeignKey(related_name='org_survey', to='onboarding_survey.FocusArea')),
                ('level_of_op', models.ForeignKey(related_name='org_survey', to='onboarding_survey.OperationLevel')),
            ],
        ),
        migrations.CreateModel(
            name='OrgSector',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sector', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='PartnerNetwork',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('network', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='PersonalGoal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('goal', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='RoleInsideOrg',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='TotalEmployee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('total', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='TotalVolunteer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('total', models.CharField(max_length=256)),
            ],
        ),
        migrations.AddField(
            model_name='organizationsurvey',
            name='partner_network',
            field=models.ForeignKey(related_name='org_survey', to='onboarding_survey.PartnerNetwork'),
        ),
        migrations.AddField(
            model_name='organizationsurvey',
            name='role_in_org',
            field=models.ForeignKey(related_name='org_survey', to='onboarding_survey.RoleInsideOrg'),
        ),
        migrations.AddField(
            model_name='organizationsurvey',
            name='sector',
            field=models.ForeignKey(related_name='org_survey', to='onboarding_survey.OrgSector'),
        ),
        migrations.AddField(
            model_name='organizationsurvey',
            name='total_employees',
            field=models.ForeignKey(related_name='org_survey', to='onboarding_survey.TotalEmployee'),
        ),
        migrations.AddField(
            model_name='organizationsurvey',
            name='total_volunteers',
            field=models.ForeignKey(related_name='org_survey', to='onboarding_survey.TotalVolunteer'),
        ),
        migrations.AddField(
            model_name='interestssurvey',
            name='capacity_areas',
            field=models.ManyToManyField(to='onboarding_survey.OrganizationalCapacityArea'),
        ),
        migrations.AddField(
            model_name='interestssurvey',
            name='inclusion_in_community',
            field=models.ForeignKey(related_name='interest_survey', to='onboarding_survey.InclusionInCommunityChoice'),
        ),
        migrations.AddField(
            model_name='interestssurvey',
            name='interested_communities',
            field=models.ManyToManyField(to='onboarding_survey.CommunityTypeInterest'),
        ),
        migrations.AddField(
            model_name='interestssurvey',
            name='personal_goal',
            field=models.ManyToManyField(to='onboarding_survey.PersonalGoal'),
        ),
    ]
