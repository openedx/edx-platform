# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.db import migrations


log = logging.getLogger(__name__)


def forwards(apps, schema_editor):
    """
    Populates data in CohortMembership table
    """
    CohortMembership = apps.get_model("course_groups", "CohortMembership")
    CourseUserGroup = apps.get_model("course_groups", "CourseUserGroup")
    for course_group in CourseUserGroup.objects.filter(group_type='cohort'):
        for user in course_group.users.all():
            membership = CohortMembership(
                course_user_group=course_group,
                user=user,
                course_id=course_group.course_id
            )
            try:
                membership.save()
            except Exception:
                log.info(
                    (
                        "Faild to add membership with course_user_group %, "
                        "user %s, "
                        "course_id %s, "
                    ),
                    unicode(course_group),
                    unicode(user),
                    unicode(course_group.course_id)
                )


def backwards(apps, schema_editor):
    """
    Removes existing data in CohortMembership
    """
    CohortMembership = apps.get_model("course_groups", "CohortMembership")
    CohortMembership.objects.all.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('course_groups', '0002_cohort_membership_model'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
