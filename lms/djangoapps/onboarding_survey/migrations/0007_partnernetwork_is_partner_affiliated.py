# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0006_auto_20170909_0512'),
    ]

    operations = [
        migrations.AddField(
            model_name='partnernetwork',
            name='is_partner_affiliated',
            field=models.BooleanField(default=False),
        ),
    ]
