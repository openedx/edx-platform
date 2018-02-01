# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='educationlevel',
            name='order',
            field=models.SmallIntegerField(unique=True, null=True),
        ),
        migrations.AddField(
            model_name='englishproficiency',
            name='order',
            field=models.SmallIntegerField(unique=True, null=True),
        ),
        migrations.AddField(
            model_name='focusarea',
            name='order',
            field=models.SmallIntegerField(unique=True, null=True),
        ),
        migrations.AddField(
            model_name='functionarea',
            name='order',
            field=models.SmallIntegerField(unique=True, null=True),
        ),
        migrations.AddField(
            model_name='operationlevel',
            name='order',
            field=models.SmallIntegerField(unique=True, null=True),
        ),
        migrations.AddField(
            model_name='orgsector',
            name='order',
            field=models.SmallIntegerField(unique=True, null=True),
        ),
        migrations.AddField(
            model_name='partnernetwork',
            name='order',
            field=models.SmallIntegerField(unique=True, null=True),
        ),
        migrations.AddField(
            model_name='roleinsideorg',
            name='order',
            field=models.SmallIntegerField(unique=True, null=True),
        ),
        migrations.AddField(
            model_name='totalemployee',
            name='order',
            field=models.SmallIntegerField(unique=True, null=True),
        ),
        migrations.AlterField(
            model_name='organizationmetric',
            name='actual_data',
            field=models.NullBooleanField(choices=[(0, b'Estimated - My answers are my best guesses based on my knowledge of the organization'), (1, b"Actual - My answers come directly from my organization's official documentation")]),
        ),
    ]
