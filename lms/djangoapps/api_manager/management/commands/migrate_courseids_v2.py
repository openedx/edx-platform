"""
One-time data migration script -- shoulen't need to run it again
"""
import logging

from django.core.management.base import BaseCommand

from api_manager import models as api_models

log = logging.getLogger(__name__)


def _migrate_course_id(old_course_id):
    course_id = old_course_id.replace("slashes:", "")
    course_id = course_id.replace("course-v1:", "")
    course_id = course_id.replace("+", "/")
    return course_id


def _migrate_content_id(old_content_id):
    if "slashes:" in old_content_id or "course-v1:" in old_content_id:
        new_content_id = self._migrate_course_id(old_content_id)
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

        log.warning('Migrating Course Groups...')
        course_groups = api_models.CourseGroupRelationship.objects.all()
        for cg in course_groups:
            cg.course_id = _migrate_course_id(cg.course_id)
            cg.save()
        log.warning('Complete!')

        log.warning('Migrating Course Content Groups...')
        course_content_groups = api_models.CourseContentGroupRelationship.objects.all()
        for ccg in course_content_groups:
            ccg.course_id = _migrate_course_id(ccg.course_id)
            ccg.content_id = _migrate_content_id(ccg.content_id)
            ccg.save()
        log.warning('Complete!')

        log.warning('Migrating Course Module Completions...')
        course_module_completions = api_models.CourseModuleCompletion.objects.all()
        for cmc in course_module_completions:
            cmc.course_id = _migrate_course_id(cmc.course_id)
            cmc.content_id = _migrate_content_id(cmc.content_id)
            if cmc.stage is not None:
                cmc.stage = _migrate_content_id(cmc.stage)
            cmc.save()
        log.warning('Complete!')
