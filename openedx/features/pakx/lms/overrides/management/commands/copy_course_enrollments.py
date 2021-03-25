from logging import getLogger
from django.core.management.base import BaseCommand

from openedx.features.pakx.lms.overrides.tasks import copy_active_course_enrollments

log = getLogger(__name__)


class Command(BaseCommand):
    """
    A management command that copies active enrollments to CourseProgressEmailModel model
    """

    help = "Send email to user with course completions and reminder to others"

    def handle(self, *args, **options):
        log.info("Copying enrollment record")
        copy_active_course_enrollments.delay()
