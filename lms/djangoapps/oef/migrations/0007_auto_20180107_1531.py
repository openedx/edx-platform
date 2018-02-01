# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oef', '0006_auto_20180107_1515'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationoefscore',
            name='external_relations_score',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationoefscore',
            name='financial_management_score',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationoefscore',
            name='fundraising_score',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationoefscore',
            name='human_resource_score',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationoefscore',
            name='leadership_score',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationoefscore',
            name='marketing_score',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationoefscore',
            name='measurement_score',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationoefscore',
            name='program_design_score',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationoefscore',
            name='strategy_score',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationoefscore',
            name='systems_score',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
    ]
