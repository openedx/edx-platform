# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import courseware.fields


class Migration(migrations.Migration):

    dependencies = [
        ('courseware', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentModuleHistoryExtended',
            fields=[
                ('id', courseware.fields.UnsignedBigIntAutoField(serialize=False, primary_key=True)),
                ('version', models.CharField(db_index=True, max_length=255, null=True, blank=True)),
                ('created', models.DateTimeField(db_index=True)),
                ('state', models.TextField(null=True, blank=True)),
                ('grade', models.FloatField(null=True, blank=True)),
                ('max_grade', models.FloatField(null=True, blank=True)),
                ('student_module', models.ForeignKey(to='courseware.StudentModule', db_constraint=False)),
            ],
            options={
                'get_latest_by': 'created',
            },
        ),
    ]
