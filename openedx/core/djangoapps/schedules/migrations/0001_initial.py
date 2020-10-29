# -*- coding: utf-8 -*-


import django.utils.timezone
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0010_auto_20170207_0458'),
    ]

    operations = [
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('active', models.BooleanField(default=True, help_text='Indicates if this schedule is actively used')),
                ('start', models.DateTimeField(help_text='Date this schedule went into effect')),
                ('upgrade_deadline', models.DateTimeField(help_text='Deadline by which the learner must upgrade to a verified seat', null=True, blank=True)),
                ('enrollment', models.OneToOneField(to='student.CourseEnrollment', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Schedule',
                'verbose_name_plural': 'Schedules',
            },
        ),
    ]
