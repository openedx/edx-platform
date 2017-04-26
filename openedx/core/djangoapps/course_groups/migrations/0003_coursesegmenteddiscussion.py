# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_groups', '0002_change_inline_default_cohort_value'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseSegmentedDiscussion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('discussion_id', models.TextField()),
                ('segmentation_scheme', models.CharField(max_length=20, choices=[(b'cohort', b'Cohort'), (b'enrollment_track', b'Enrollment Track')])),
                ('course_cohorts_settings', models.ForeignKey(related_name='segmented_discussions', to='course_groups.CourseCohortsSettings')),
            ],
        ),
    ]
