# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0012_auto_20180228_0848'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicaluserextendedprofile',
            name='function_stakeholder_engagement',
            field=models.SmallIntegerField(default=0, verbose_name=b'External relations and partnerships'),
        ),
        migrations.AlterField(
            model_name='historicaluserextendedprofile',
            name='interest_stakeholder_engagement',
            field=models.SmallIntegerField(default=0, verbose_name=b'External relations and partnerships'),
        ),
        migrations.AlterField(
            model_name='userextendedprofile',
            name='function_stakeholder_engagement',
            field=models.SmallIntegerField(default=0, verbose_name=b'External relations and partnerships'),
        ),
        migrations.AlterField(
            model_name='userextendedprofile',
            name='interest_stakeholder_engagement',
            field=models.SmallIntegerField(default=0, verbose_name=b'External relations and partnerships'),
        ),
    ]
