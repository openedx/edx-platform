# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CourseOverview',
            fields=[
                ('id', xmodule_django.models.CourseKeyField(max_length=255, serialize=False, primary_key=True, db_index=True)),
                ('_location', xmodule_django.models.UsageKeyField(max_length=255)),
                ('display_name', models.TextField(null=True)),
                ('display_number_with_default', models.TextField()),
                ('display_org_with_default', models.TextField()),
                ('start', models.DateTimeField(null=True)),
                ('end', models.DateTimeField(null=True)),
                ('advertised_start', models.TextField(null=True)),
                ('course_image_url', models.TextField()),
                ('facebook_url', models.TextField(null=True)),
                ('social_sharing_url', models.TextField(null=True)),
                ('end_of_course_survey_url', models.TextField(null=True)),
                ('certificates_display_behavior', models.TextField(null=True)),
                ('certificates_show_before_end', models.BooleanField(default=False)),
                ('has_any_active_web_certificate', models.BooleanField(default=False)),
                ('cert_name_short', models.TextField()),
                ('cert_name_long', models.TextField()),
                ('lowest_passing_grade', models.DecimalField(null=True, max_digits=5, decimal_places=2)),
                ('mobile_available', models.BooleanField(default=False)),
                ('visible_to_staff_only', models.BooleanField(default=False)),
                ('_pre_requisite_courses_json', models.TextField()),
            ],
        ),
    ]
