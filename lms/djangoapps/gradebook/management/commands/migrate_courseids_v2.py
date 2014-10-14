"""
One-time data migration script -- shoulen't need to run it again
"""
import logging

from django.core.management.base import BaseCommand

from opaque_keys.edx.keys import CourseKey
from gradebook import models

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Migrates legacy course/content identifiers across several models to the new format
    """

    def handle(self, *args, **options):

        log.warning('Migrating Student Gradebook Entries...')
        gradebook_entries = models.StudentGradebook.objects.all()
        for gbe in gradebook_entries:
            current_course_id = unicode(gbe.course_id)
            oldstyle_course_id = current_course_id.replace("slashes:", "")
            oldstyle_course_id = current_course_id.replace("+", "/")
            gbe.course_id = CourseKey.from_string(oldstyle_course_id)
            gbe.save()
        log.warning('Complete!')

        log.warning('Migrating Student Gradebook History Entries...')
        history_entries = models.StudentGradebookHistory.objects.all()
        for he in history_entries:
            current_course_id = unicode(he.course_id)
            oldstyle_course_id = current_course_id.replace("slashes:", "")
            oldstyle_course_id = current_course_id.replace("+", "/")
            he.course_id = oldstyle_course_id
            he.save()
        log.warning('Complete!')
