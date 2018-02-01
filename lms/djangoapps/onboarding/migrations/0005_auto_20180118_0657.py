# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0002_populate_initial_data'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='educationlevel',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='englishproficiency',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='focusarea',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='functionarea',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='operationlevel',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='orgsector',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='partnernetwork',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='roleinsideorg',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='totalemployee',
            options={'ordering': ['order']},
        ),
        migrations.RemoveField(
            model_name='userextendedprofile',
            name='level_of_education',
        ),
        migrations.AlterField(
            model_name='historicaluserextendedprofile',
            name='function_marketing_communication',
            field=models.SmallIntegerField(default=0, verbose_name=b'Marketing, communications, and PR'),
        ),
        migrations.AlterField(
            model_name='historicaluserextendedprofile',
            name='goal_relation_with_other',
            field=models.SmallIntegerField(default=0, verbose_name=b'Build relationships with other nonprofit leaders'),
        ),
        migrations.AlterField(
            model_name='historicaluserextendedprofile',
            name='level_of_education',
            field=models.CharField(max_length=30, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationpartner',
            name='partner',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='userextendedprofile',
            name='function_marketing_communication',
            field=models.SmallIntegerField(default=0, verbose_name=b'Marketing, communications, and PR'),
        ),
        migrations.AlterField(
            model_name='userextendedprofile',
            name='goal_relation_with_other',
            field=models.SmallIntegerField(default=0, verbose_name=b'Build relationships with other nonprofit leaders'),
        ),
    ]
