# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0010_auto_20170207_0458'),
    ]

    operations = [
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('active', models.BooleanField(default=True, help_text='Indicates if this schedule is actively used')),
                ('start', models.DateTimeField(help_text='Date this schedule went into effect')),
                ('upgrade_deadline', models.DateTimeField(help_text='Deadline by which the learner must upgrade to a verified seat', null=True, blank=True)),
                ('enrollment', models.OneToOneField(to='student.CourseEnrollment')),
            ],
            options={
                'verbose_name': 'Schedule',
                'verbose_name_plural': 'Schedules',
            },
        ),
    ]
