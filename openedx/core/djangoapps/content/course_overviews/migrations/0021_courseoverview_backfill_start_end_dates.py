# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import migrations


def copy_column_values(apps, schema_editor):
    """
    Copy start,end into start_date & end_date respectively
    """
    CourseOverview = apps.get_model('course_overviews', 'CourseOverview')
    HistoricalCourseOverview = apps.get_model('course_overviews', 'HistoricalCourseOverview')

    # Do not create historical rows for these changes, we will update historical records directly
    CourseOverview.skip_history_when_saving = True

    # Currently there are ~14k of these
    for course_overview in CourseOverview.objects.all():
        course_overview.start_date = course_overview.start
        course_overview.end_date = course_overview.end
        course_overview.save()

    # Currently there are ~505k of these
    for historical_course_overview in HistoricalCourseOverview.objects.all():
        historical_course_overview.start_date = historical_course_overview.start
        historical_course_overview.end_date = historical_course_overview.end
        historical_course_overview.save()


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0020_courseoverviewtab_url_slug'),
    ]

    operations = [
        migrations.RunPython(
            copy_column_values,
            reverse_code=migrations.RunPython.noop,  # Allow reverse migrations, but make it a no-op.
        ),
    ]
