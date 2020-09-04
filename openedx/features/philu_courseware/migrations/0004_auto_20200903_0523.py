# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0020_auto_20200618_0157'),
        ('philu_courseware', '0003_competencyassessmentrecord_question_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseEnrollmentMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('program_uuid', models.UUIDField(blank=True, null=True, verbose_name='Program UUID')),
                ('course_enrollment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='course_enrollment_meta', related_query_name='course_enrollment_meta', to='student.CourseEnrollment')),
            ],
        ),
    ]
