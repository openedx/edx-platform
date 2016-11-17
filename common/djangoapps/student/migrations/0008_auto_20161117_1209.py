# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0007_registrationcookieconfiguration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='level_of_education',
            field=models.CharField(blank=True, max_length=6, null=True, db_index=True, choices=[(b'p', b'Doctorate'), (b'm', b"Master's or professional degree"), (b'b', b"Bachelor's degree"), (b'a', b'Associate degree'), (b'hs', b'Secondary/high school'), (b'jhs', b'Junior secondary/junior high/middle school'), (b'el', b'Elementary/primary school'), (b'none', b'No formal education'), (b'other', b'Other education')]),
        ),
    ]
