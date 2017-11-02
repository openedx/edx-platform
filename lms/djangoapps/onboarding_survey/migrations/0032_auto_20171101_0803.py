# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.core.validators
import lms.djangoapps.onboarding_survey.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('onboarding_survey', '0034_auto_20171101_0349'),
    ]

    operations = [
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('alphabetic_code', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='FunctionArea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='OrganizationDetailSurvey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('can_provide_info', models.BooleanField(default=True, choices=[(1, b'Yes'), (0, b'No')])),
                ('info_accuracy', models.NullBooleanField(choices=[(1, b"Actual - My answers come directly from my organization's official documentation"), (0, b'Estimated - My answers are my best guesses based on my knowledge of the organization')])),
                ('last_fiscal_year_end_date', models.DateField(null=True, blank=True)),
                ('total_clients', models.PositiveIntegerField(null=True, blank=True)),
                ('total_employees', models.PositiveIntegerField(null=True, blank=True)),
                ('total_revenue', models.BigIntegerField(null=True, blank=True)),
                ('total_expenses', models.BigIntegerField(null=True, blank=True)),
                ('total_program_expenses', models.BigIntegerField(null=True, blank=True)),
                ('currency', models.ForeignKey(related_name='org_detail_survey', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='onboarding_survey.Currency', null=True)),
                ('user', models.OneToOneField(related_name='org_detail_survey', null=True, blank=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='extendedprofile',
            name='is_currently_employed',
        ),
        migrations.RemoveField(
            model_name='interestssurvey',
            name='reason_of_selected_interest',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='is_poc_exist',
        ),
        migrations.RemoveField(
            model_name='organizationsurvey',
            name='role_in_org',
        ),
        migrations.RemoveField(
            model_name='organizationsurvey',
            name='start_month_year',
        ),
        migrations.RemoveField(
            model_name='organizationsurvey',
            name='total_clients',
        ),
        migrations.RemoveField(
            model_name='organizationsurvey',
            name='total_revenue',
        ),
        migrations.RemoveField(
            model_name='organizationsurvey',
            name='total_volunteers',
        ),
        migrations.RemoveField(
            model_name='userinfosurvey',
            name='dob',
        ),
        migrations.AddField(
            model_name='organization',
            name='admin',
            field=models.ForeignKey(related_name='organization', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='organizationsurvey',
            name='alternate_admin_email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='organizationsurvey',
            name='is_org_url_exist',
            field=models.BooleanField(default=True, choices=[(1, b'Yes'), (0, b'No')]),
        ),
        migrations.AddField(
            model_name='userinfosurvey',
            name='role_in_org',
            field=models.ForeignKey(related_name='user_info_survey', to='onboarding_survey.RoleInsideOrg', null=True),
        ),
        migrations.AddField(
            model_name='userinfosurvey',
            name='start_month_year',
            field=models.CharField(default='1980-01', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userinfosurvey',
            name='weekly_work_hours',
            field=models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(168)]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userinfosurvey',
            name='year_of_birth',
            field=models.PositiveIntegerField(default=1960, validators=[django.core.validators.MinValueValidator(1900), django.core.validators.MaxValueValidator(2017)]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='interestssurvey',
            name='capacity_areas',
            field=models.ManyToManyField(to='onboarding_survey.OrganizationalCapacityArea', blank=True),
        ),
        migrations.AlterField(
            model_name='interestssurvey',
            name='interested_communities',
            field=models.ManyToManyField(to='onboarding_survey.CommunityTypeInterest', blank=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='city',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='country',
            field=models.CharField(max_length=255),
        ),
        migrations.RemoveField(
            model_name='organizationsurvey',
            name='partner_network',
        ),
        migrations.AddField(
            model_name='organizationsurvey',
            name='partner_network',
            field=models.ManyToManyField(to='onboarding_survey.PartnerNetwork'),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='total_employees',
            field=models.ForeignKey(related_name='org_survey', to='onboarding_survey.TotalEmployee', null=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='url',
            field=models.URLField(blank=True, max_length=255, validators=[lms.djangoapps.onboarding_survey.models.SchemaOrNoSchemaURLValidator]),
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='city_of_employment',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='city_of_residence',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='country_of_employment',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='country_of_residence',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='language',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='userinfosurvey',
            name='level_of_education',
            field=models.ForeignKey(related_name='user_info_survey', to='onboarding_survey.EducationLevel', null=True),
        ),
        migrations.AddField(
            model_name='userinfosurvey',
            name='function_area',
            field=models.ManyToManyField(to='onboarding_survey.FunctionArea', null=True, blank=True),
        ),
    ]
