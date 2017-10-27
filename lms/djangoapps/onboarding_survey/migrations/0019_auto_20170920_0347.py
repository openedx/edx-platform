# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0018_extendedprofile_org_admin_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='extendedprofile',
            name='are_surveys_complete',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='extendedprofile',
            name='org_admin_email',
            field=models.EmailField(default=b'', max_length=254, blank=True),
        ),
    ]
