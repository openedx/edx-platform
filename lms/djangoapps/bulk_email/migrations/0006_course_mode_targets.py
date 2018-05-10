# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_modes', '0007_coursemode_bulk_sku'),
        ('bulk_email', '0005_move_target_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseModeTarget',
            fields=[
                ('target_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='bulk_email.Target')),
                ('track', models.ForeignKey(to='course_modes.CourseMode')),
            ],
            bases=('bulk_email.target',),
        ),
        migrations.AlterField(
            model_name='target',
            name='target_type',
            field=models.CharField(max_length=64, choices=[(b'myself', b'Myself'), (b'staff', b'Staff and instructors'), (b'learners', b'All students'), (b'cohort', b'Specific cohort'), (b'track', b'Specific course mode')]),
        ),
    ]
