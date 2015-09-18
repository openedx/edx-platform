# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courseware', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PsychometricData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('done', models.BooleanField(default=False)),
                ('attempts', models.IntegerField(default=0)),
                ('checktimes', models.TextField(null=True, blank=True)),
                ('studentmodule', models.OneToOneField(to='courseware.StudentModule')),
            ],
        ),
    ]
