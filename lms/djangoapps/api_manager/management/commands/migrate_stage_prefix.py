"""
One-time data migration script -- shouldn't need to run it again
"""
import logging

from django.core.management.base import BaseCommand

from progress.models import CourseModuleCompletion

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Migrates legacy course/content identifiers across several models to the new format
    """

    def handle(self, *args, **options):
        log.warning('Migrating Course Module Completions Stage Field...')
        course_module_completions = CourseModuleCompletion.objects.all()
        for cmc in course_module_completions:
            if cmc.stage is not None:
                cmc.stage = cmc.stage.replace("i4x://", "")
                cmc.save()
        log.warning('Complete!')
