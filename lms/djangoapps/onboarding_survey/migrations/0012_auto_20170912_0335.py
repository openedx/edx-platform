# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0011_auto_20170912_0329'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationsurvey',
            name='city',
            field=models.CharField(max_length=265, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='founding_year',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='partner_network',
            field=models.ForeignKey(related_name='org_survey', blank=True, to='onboarding_survey.PartnerNetwork', null=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='role_in_org',
            field=models.ForeignKey(related_name='org_survey', blank=True, to='onboarding_survey.RoleInsideOrg', null=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='state_mon_year',
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='total_annual_clients_or_beneficiary',
            field=models.PositiveIntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='total_annual_revenue_for_last_fiscal',
            field=models.CharField(max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='total_employees',
            field=models.ForeignKey(related_name='org_survey', blank=True, to='onboarding_survey.TotalEmployee', null=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='total_volunteers',
            field=models.ForeignKey(related_name='org_survey', blank=True, to='onboarding_survey.TotalVolunteer', null=True),
        ),
        migrations.AlterField(
            model_name='organizationsurvey',
            name='url',
            field=models.URLField(max_length=256, blank=True),
        ),
    ]
