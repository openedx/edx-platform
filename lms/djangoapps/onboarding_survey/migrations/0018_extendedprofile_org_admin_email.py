# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0017_auto_20170916_1119'),
    ]

    operations = [
        migrations.AddField(
            model_name='extendedprofile',
            name='org_admin_email',
            field=models.EmailField(max_length=254, blank=True),
        ),
    ]
