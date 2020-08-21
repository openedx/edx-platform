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
    Auto Score ORA assessment for On Demand Course if learner has completed all the necessary steps i-e
    submitted their responses, assess required peers responses and finally own assessment if required, if that
    learner ends up in a waiting queue after certain (configurable) days of response submission this command will
    auto-score the learner ORA assessment for those users. The no of days to wait to auto-score ORA is configurable
    from site configurations model though its default value is 3 days.
    """

    def handle(self, *args, **options):
        course_ids = CourseOverview.objects.filter(self_paced=True).values_list('id', flat=True)

        # Get unfinished assessment workflows uuids
        workflows_uuids = AssessmentWorkflow.objects.filter(course_id__in=course_ids).values_list(
            'submission_uuid', flat=True).exclude(status__in=['done', 'cancelled'])

        if not workflows_uuids:
            log.info('No pending open assessment found to autoscore. No ORA in progress')
            return  # nothing to auto-score

        enrollments = CourseEnrollment.objects.filter(course_id__in=course_ids, is_active=True)

        find_and_autoscore_submissions(
            enrollments=enrollments,
            workflows_uuids=workflows_uuids
        )
