# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('onboarding', '0001_initial'),
        ('oef', '0002_auto_20171130_0231'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationOefScore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('start_date', models.DateField()),
                ('finish_date', models.DateField()),
                ('version', models.CharField(default=b'v1.0', max_length=10)),
                ('human_resource_score', models.PositiveIntegerField()),
                ('leadership_score', models.PositiveIntegerField()),
                ('financial_management_score', models.PositiveIntegerField()),
                ('fundraising_score', models.PositiveIntegerField()),
                ('measurement_score', models.PositiveIntegerField()),
                ('marketing_score', models.PositiveIntegerField()),
                ('strategy_score', models.PositiveIntegerField()),
                ('program_design_score', models.PositiveIntegerField()),
                ('external_relations_score', models.PositiveIntegerField()),
                ('systems_score', models.PositiveIntegerField()),
                ('org', models.ForeignKey(related_name='organization_oef_scores', to='onboarding.Organization')),
                ('user', models.ForeignKey(related_name='organization_oef_scores', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
