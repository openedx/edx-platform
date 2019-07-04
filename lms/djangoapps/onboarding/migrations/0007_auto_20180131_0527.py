# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding', '0006_auto_20180131_0801'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicaluserextendedprofile',
            name='level_of_education',
            field=models.CharField(max_length=90, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='organizationadminhashkeys',
            name='suggested_admin_email',
            field=models.EmailField(max_length=254),
        ),
    ]
