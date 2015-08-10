"""
One-time data migration script -- shoulen't need to run it again
"""
import logging

from django.core.management.base import BaseCommand

from opaque_keys.edx.keys import CourseKey
from gradebook import models

log = logging.getLogger(__name__)


def _migrate_course_id(old_course_id):
    course_id = old_course_id.replace("slashes:", "")
    course_id = course_id.replace("course-v1:", "")
    course_id = course_id.replace("+", "/")
    return course_id


def _migrate_content_id(old_content_id):
    if "slashes:" in old_content_id or "course-v1:" in old_content_id:
        new_content_id = _migrate_course_id(old_content_id)
    else:
        content_id = old_content_id.replace("location:", "")
        content_components = content_id.split('+')
        new_content_id = "i4x:/"
        for x in range(0, len(content_components)):
            if x != 2:
                new_content_id = "{}/{}".format(new_content_id, content_components[x])
    return new_content_id


class Command(BaseCommand):
    """
    Migrates legacy course/content identifiers across several models to the new format
    """

    def handle(self, *args, **options):

        log.warning('Migrating Student Gradebook Entries...')
        gradebook_entries = models.StudentGradebook.objects.all()
        for gbe in gradebook_entries:
            course_id = _migrate_course_id(unicode(gbe.course_id))
            print course_id
            gbe.course_id = CourseKey.from_string(course_id)
            gbe.save()
        log.warning('Complete!')

        log.warning('Migrating Student Gradebook History Entries...')
        history_entries = models.StudentGradebookHistory.objects.all()
        for he in history_entries:
            course_id = _migrate_course_id(unicode(he.course_id))
            he.course_id = CourseKey.from_string(course_id)
            he.save()
        log.warning('Complete!')
