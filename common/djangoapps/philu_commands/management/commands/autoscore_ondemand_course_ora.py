"""
Command to auto score ORA.
"""
from logging import getLogger

from django.core.management.base import BaseCommand

from openassessment.workflow.models import AssessmentWorkflow
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.assessment.helpers import find_and_autoscore_submissions
from student.models import CourseEnrollment

log = getLogger(__name__)


class Command(BaseCommand):
    """
    Auto Score ORA assessment for on demand course
    """
    help = """
    Auto score ORA assessment for on demand course, if learner has completed step 1 i.e. ORA submission, a certain
    number of days days ago. This value for number of days is configurable from site configurations model though its
    default value is 3 days.
    """

    def handle(self, *args, **options):
        ondemand_course_ids = CourseOverview.objects.filter(self_paced=True).values_list('id', flat=True)

        submission_uuids = AssessmentWorkflow.objects.filter(course_id__in=ondemand_course_ids).values_list(
            'submission_uuid', flat=True).exclude(status__in=['done', 'cancelled'])

        if not submission_uuids:
            log.info('No pending open response assessment found to autoscore. No ORA in progress')
            return

        enrollments = CourseEnrollment.objects.filter(course_id__in=ondemand_course_ids, is_active=True)

        find_and_autoscore_submissions(enrollments=enrollments, submission_uuids=submission_uuids)
