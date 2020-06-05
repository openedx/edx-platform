from logging import getLogger

from pytz import utc
from datetime import datetime
from django.core.management.base import BaseCommand

from submissions.models import Submission
from student.models import CourseEnrollment, AnonymousUserId
from openassessment.workflow.models import AssessmentWorkflow

from xmodule.modulestore.django import modulestore
from openedx.features.assessment.helpers import autoscore_ora
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = getLogger(__name__)

DAYS_TO_WAIT_AUTO_ASSESSMENT = 14


class Command(BaseCommand):
    help = """
        Auto Score ORA assesment for On Demand Course if learner has completed all the necessary steps i-e 
        submitted their responses, assess required peers responses and finally own assessment if required, if that 
        learner ends up in a waiting queue after 2 weeks of response submission this command will auto-score the
        learner ORA assessment for those users. 
    """

    def handle(self, *args, **options):

        courses = CourseOverview.objects.filter(self_paced=True)

        for course in courses:
            enrollments = CourseEnrollment.objects.filter(course_id=course.id, is_active=True)

            for enrollment in enrollments:

                today = datetime.now(utc).date()
                delta_days = today - enrollment.created.date()
                current_module = (delta_days.days / 7) + 1
                user = enrollment.user

                if current_module < 3:
                    log.info('Current module is less than 3')
                    continue

                else:
                    max_module = 1

                    course_chapters = modulestore().get_items(
                        course.id,
                        qualifiers={'category': 'course'}
                    )
                    for index_chapter, chapter in enumerate(course_chapters[0].children):
                        if max_module < current_module:
                            sequentials = modulestore().get_item(chapter)
                            for index_sequential, sequential in enumerate(sequentials.children):
                                verticals = modulestore().get_item(sequential)
                                for index_vertical, vertical in enumerate(verticals.children):
                                    vertical_blocks = modulestore().get_item(vertical)
                                    for index_block, block in enumerate(vertical_blocks.children):
                                        if block.block_type == 'openassessment':

                                            try:
                                                anonymous_user = AnonymousUserId.objects.get(user=user,
                                                                                             course_id=course.id)
                                            except AnonymousUserId.DoesNotExist:
                                                log.info('Anonymous Id does not exist for User: {user}'.format(
                                                    user=user
                                                ))
                                                continue
                                            except AnonymousUserId.MultipleObjectsReturned:
                                                log.info('Multiple Anonymous Ids for User: {user}'.format(user=user))
                                                continue

                                            response_submission = Submission.objects.filter(
                                                student_item__student_id=anonymous_user.anonymous_user_id,
                                                student_item__item_id=block).first()
                                            if not response_submission:
                                                continue
                                            log.info('Response Created at: {created_date}'.format(
                                                created_date=response_submission.created_at.date()
                                            ))

                                            response_submission_delta = today - response_submission.created_at.date()

                                            # check if this chapter is 2 weeks older or not.
                                            module_access_days = delta_days.days - (index_chapter * 7)

                                            if (module_access_days >= DAYS_TO_WAIT_AUTO_ASSESSMENT and
                                                    response_submission_delta.days >= DAYS_TO_WAIT_AUTO_ASSESSMENT):
                                                try:
                                                    # Status[0] is the status of assessment that are in waiting mode
                                                    AssessmentWorkflow.objects.get(
                                                        status=AssessmentWorkflow.STATUSES[0],
                                                        course_id=course.id,
                                                        item_id=block,
                                                        submission_uuid=response_submission.uuid
                                                    )
                                                    student = {
                                                        'id': user.id,
                                                        'username': user.username,
                                                        'email': user.email,
                                                        'anonymous_user_id': anonymous_user.anonymous_user_id
                                                    }
                                                    autoscore_ora(course.id, unicode(block), student)
                                                except AssessmentWorkflow.DoesNotExist:
                                                    continue

                        max_module = max_module + 1
