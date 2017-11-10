# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onboarding_survey', '0037_auto_20171107_0434'),
    ]

    operations = [
        migrations.AddField(
            model_name='extendedprofile',
            name='admin_activation_key',
            field=models.CharField(default=None,null=True,blank=True, max_length=32, verbose_name=b'admin activation key'),
        ),
        migrations.AddField(
            model_name='extendedprofile',
            name='is_admin_activated',
            field=models.BooleanField(default=False),
        ),
    ]
