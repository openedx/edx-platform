"""
One-time data migration script -- shoulen't need to run it again
"""
import logging

from django.core.management.base import BaseCommand

from api_manager import models as api_models

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Migrates legacy course/content identifiers across several models to the new format
    """

    def handle(self, *args, **options):

        log.warning('Migrating Course Groups...')
        course_groups = api_models.CourseGroupRelationship.objects.all()
        for cg in course_groups:
            current_course_id = cg.course_id
            oldstyle_course_id = current_course_id.replace("slashes:", "")
            oldstyle_course_id = oldstyle_course_id.replace("+", "/")
            cg.course_id = oldstyle_course_id
            cg.save()
        log.warning('Complete!')

        log.warning('Migrating Course Content Groups...')
        course_content_groups = api_models.CourseContentGroupRelationship.objects.all()
        for ccg in course_content_groups:
            current_course_id = ccg.course_id
            oldstyle_course_id = current_course_id.replace("slashes:", "")
            oldstyle_course_id = oldstyle_course_id.replace("+", "/")
            ccg.course_id = oldstyle_course_id

            current_content_id = ccg.content_id
            oldstyle_content_id = current_content_id.replace("slashes:", "")
            oldstyle_content_id = oldstyle_content_id.replace("+", "/")
            ccg.content_id = oldstyle_content_id
            ccg.save()
        log.warning('Complete!')

        log.warning('Migrating Course Module Completions...')
        course_module_completions = api_models.CourseModuleCompletion.objects.all()
        for cmc in course_module_completions:
            current_course_id = cmc.course_id
            oldstyle_course_id = current_course_id.replace("slashes:", "")
            oldstyle_course_id = oldstyle_course_id.replace("+", "/")
            cmc.course_id = oldstyle_course_id

            current_content_id = cmc.content_id
            oldstyle_content_id = current_content_id.replace("slashes:", "")
            oldstyle_content_id = oldstyle_content_id.replace("+", "/")
            cmc.content_id = oldstyle_content_id

            if cmc.stage is not None:
                current_stage = cmc.stage
                oldstyle_stage = current_stage.replace("slashes:", "")
                oldstyle_stage = oldstyle_stage.replace("+", "/")
                cmc.stage = oldstyle_stage
                cmc.save()
        log.warning('Complete!')
