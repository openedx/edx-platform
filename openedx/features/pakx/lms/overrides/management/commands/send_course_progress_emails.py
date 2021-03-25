from logging import getLogger
from django.core.management.base import BaseCommand

from openedx.features.pakx.lms.overrides.tasks import check_and_send_email_to_course_learners

log = getLogger(__name__)


class Command(BaseCommand):
    """
    A management command that checks enrollment in active courses and sends email for course completion and
    reminder if course is about to end and no completed.
    """

    help = "Send email to user with course completions and reminder to others"

    def handle(self, *args, **options):
        log.info("Staring command to check active course progress")
        check_and_send_email_to_course_learners.delay()
