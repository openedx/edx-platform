# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0009_auto_20170213_0236'),
    ]

    operations = [
        migrations.CreateModel(
            name='CandidateReference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('phone_number', models.CharField(max_length=20)),
                ('position', models.CharField(max_length=255)),
            ],
        ),
        migrations.RemoveField(
            model_name='candidateprofile',
            name='references',
        ),
        migrations.AddField(
            model_name='candidatereference',
            name='candidate',
            field=models.ForeignKey(to='student.CandidateProfile', null=True),
        ),
    ]
