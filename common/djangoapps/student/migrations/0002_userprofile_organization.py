# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appsembler_lms', '0001_initial'),
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='organization',
            field=models.ForeignKey(to='appsembler_lms.Organization', null=True),
        ),
    ]
