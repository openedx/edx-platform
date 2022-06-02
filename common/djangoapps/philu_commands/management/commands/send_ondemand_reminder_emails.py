"""
A command for sending reminder emails to students who have not completed graded modules
"""
from datetime import datetime, timedelta
from logging import getLogger

from django.core.management.base import BaseCommand
from submissions.models import Submission

from common.lib.hubspot_client.client import HubSpotClient
from common.lib.hubspot_client.tasks import task_send_hubspot_email
from lms.djangoapps.onboarding.helpers import get_email_pref_on_demand_course, get_user_anonymous_id
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.ondemand_email_preferences.helpers import get_my_account_link
from openedx.features.philu_courseware.helpers import get_nth_chapter_link
from philu_commands.helpers import generate_course_structure
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

log = getLogger(__name__)

today = datetime.now().date()
DAYS_FOR_EACH_MODULE = 7
INACTIVITY_REMINDER_DAYS = 10
ORA_ASSESSMENT_BLOCK = 'openassessment'


class Command(BaseCommand):
    """
    A command to send reminder emails to those users who haven't completed the scheduled graded module for 10 days.
    This email will not be sent for those modules which don't have at-least one graded sub-section.
    """

    help = """
        Send reminder emails to those users who haven't completed the scheduled graded module for 10 days.
        This email will not be sent for those module which don't have at-least one graded sub-section.
    """

    def handle(self, *args, **options):

        # Getting all self paced courses with end dates greater than today (Only active ones).
        courses = CourseOverview.objects.filter(self_paced=True, end__gte=today)

        for course in courses:
            course_struct = generate_course_structure(course.id)['structure']

            if not course_struct:
                log.error('Course doesn\'t have a proper structure.')
                continue

            ora_blocks = get_all_ora_blocks(course_struct)

            # If course doesn't have any ORA blocks, continue.
            if not ora_blocks:
                continue

            course_blocks = course_struct['blocks']

            graded_oras_count = get_graded_ora_count(ora_blocks)
            last_module_oras = get_last_module_ora(course_blocks)

            # Getting all enrollments of user in self paced course.
            enrollments = CourseEnrollment.objects.filter(course_id=course.id, is_active=True)

            for enrollment in enrollments:
                user = enrollment.user

                try:
                    anonymous_user = get_user_anonymous_id(user, course.id)
                except Exception as error:  # pylint: disable=broad-except
                    log.info(error)
                    continue

                # If user hasn't enable email preferences for on demand course, no need to go further.
                if not get_email_pref_on_demand_course(user, course.id):
                    continue

                course_chapters = modulestore().get_items(
                    course.id,
                    qualifiers={'category': 'course'}
                )

                course_deadline = get_suggested_course_deadline(enrollment.created.date(), course_chapters[0].children)

                # Get all user submission in descending order by date
                response_submissions = Submission.objects.filter(
                    student_item__student_id=anonymous_user.anonymous_user_id,
                    student_item__course_id=course.id.to_deprecated_string()).order_by('-created_at')

                # Check if user has submitted last modules graded oras or not. If yes no need to send email OR
                # If user's submission gets equal to graded oras count than don't need to continue.
                if (last_module_oras and check_for_last_module_submission(last_module_oras, anonymous_user)) or \
                        len(response_submissions) == graded_oras_count:
                    log.info('Last module Graded ORAs submitted so no further check')
                    continue

                latest_submission = response_submissions.first()

                if not response_submissions.exists():
                    if has_inactivity_threshold_reached(enrollment.created.date(), today):
                        send_reminder_email(user, course, course_deadline)
                    continue

                # Check for latest submission entry from submission table if the difference of created date and
                # today is equals to "INACTIVITY_REMINDER_DAYS" days this means that email should be send to user
                # but before that we need to check is it the first time user shows an inactivity for
                # "INACTIVITY_REMINDER_DAYS" days or not if yes than send email else means that emails has already
                #  been sent to user so no need to send it again.
                if has_inactivity_threshold_reached(latest_submission.created_at.date(), today):
                    log.info('Inactivity threshold reached so check for previous ORAs')
                    last_response_time = latest_submission.created_at.date()

                    # Boolean to keep track if user has shown an inactivity for "INACTIVITY_REMINDER_DAYS"
                    is_threshold_reached_before = False

                    # We have checked first entry separately so starting from second index.
                    for response in response_submissions[1:]:
                        if has_inactivity_threshold_reached(response.created_at.date(), last_response_time):
                            log.info('User showed inactivity previously')
                            is_threshold_reached_before = True
                            break
                        last_response_time = response.created_at.date()

                    # If user haven't been inactive in past before today than send email.
                    if not is_threshold_reached_before:
                        send_reminder_email(user, course, course_deadline)


def has_inactivity_threshold_reached(first_date, second_date):
    return True if (second_date - first_date).days == INACTIVITY_REMINDER_DAYS else False


def get_suggested_course_deadline(enrollment_date, chapters):
    return enrollment_date + timedelta(days=(len(chapters) * DAYS_FOR_EACH_MODULE))


def get_graded_ora_count(oras_block):
    """
    Get total number of graded ORAs

    Args:
        oras_block (list): List of ORAs

    Returns:
        int: Number of graded ORAs
    """
    graded_ora_count = 0

    for ora in oras_block:
        if ora['graded']:
            graded_ora_count += 1

    return graded_ora_count


def get_all_ora_blocks(course_struct):
    """
    Get all ORAs is a course

    Args:
        course_struct (dict): Course structure dict

    Returns:
        List: List of ORAs units
    """
    ora_blocks = []

    for block in course_struct['blocks'].itervalues():
        if block['block_type'] == ORA_ASSESSMENT_BLOCK:
            ora_blocks.append(block)

    return ora_blocks


def get_last_module_ora(course_blocks):
    """
    Get a list of last module ORAs

    Args:
        course_blocks (dict): Course blocks dict

    Returns:
        List: List of ORAs units
    """
    last_module_oras = []

    for block in course_blocks.itervalues():
        if block['block_type'] != 'course':
            continue
        course_children = block['children']
        final_chapter_block = course_children[-1]
        chapter_children = course_blocks[final_chapter_block]['children']

        for sequential in chapter_children:
            if not course_blocks[sequential]['graded']:
                continue
            sequential_children = course_blocks[sequential]['children']

            for vertical in sequential_children:

                for unit in course_blocks[vertical]['children']:
                    if course_blocks[unit]['block_type'] == ORA_ASSESSMENT_BLOCK:
                        last_module_oras.append(unit)

    return last_module_oras


def check_for_last_module_submission(oras_list, anonymous_user):
    """
    Check if user has submitted ORAs

    Args:
        oras_list (List): List of ORAs units
        anonymous_user (AnonymousUserId): Model object with id associated to anonymous user

    Returns:
        boolean: False if user have not submitted any ORA, True otherwise
    """
    for ora in oras_list:
        try:
            Submission.objects.get(
                student_item__student_id=anonymous_user.anonymous_user_id,
                student_item__item_id=ora)
        except Submission.DoesNotExist:
            return False

    return True


def send_reminder_email(user, course, course_deadline):
    """
    Send weekly emails for completed module

    Parameters:
    user: user, whom we are sending emails.
    course: Course for which we want to send email.
    course_deadline: Suggested deadline by which user must complete course.
    """
    next_chapter_url = get_nth_chapter_link(course, chapter_index=0)
    context = {
        'emailId': HubSpotClient.ON_DEMAND_REMINDER_EMAIL_TEMPLATE,
        'message': {
            'to': user.email
        },
        'customProperties': {
            'first_name': user.first_name,
            'course_name': course.display_name,
            'deadline_date': str(course_deadline),
            'course_url': next_chapter_url,
            'email_address': user.email,
            'unsubscribe_link': get_my_account_link(course.id)
        }
    }

    task_send_hubspot_email.delay(context)
    log.info("Emailing to %s Task Completed for course reminder", user.email)
