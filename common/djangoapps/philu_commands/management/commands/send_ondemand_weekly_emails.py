"""
Command to send on-demand weekly emails.
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

HOURS_TO_WAIT_FOR_EMAIL = 24
today = datetime.now().date()
ORA_ASSESSMENT_BLOCK = 'openassessment'
EMAIL_SUBJECT_LINE = 'Get started on the next module of {course_name}'
ON_DEMAND_MODULE_TEXT_FOMATTER = "<li> {module_name} </li>"


class Command(BaseCommand):
    """
    Command class for send on-demand weekly emails
    """
    help = """
    Send weekly emails to those users who have completed graded module in last 24 hours. This email will not be
    sent for those modules which don't have at-least one graded sub-section. If user has completed last module and
    skipped some graded modules then skip module email will be sent.
    """

    def handle(self, *args, **options):  # pylint: disable=too-many-statements
        # Getting all self paced courses.
        courses = CourseOverview.objects.filter(self_paced=True)

        # TODO This command have too many nested blocks, which needs an update.
        # pylint: disable=too-many-nested-blocks
        for course in courses:
            course_struct = generate_course_structure(course.id)['structure']

            if not course_struct:
                log.error('Course doesn\'t have a proper structure.')
                continue

            course_blocks = course_struct['blocks']
            # If course doesn't have any blocks, continue.
            if not course_blocks:
                continue

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

                chapters_skipped = {}
                all_chapters = course_chapters[0].children
                last_chapter_index = (len(all_chapters) - 1)

                # We introduced this variable to store submission date of ora in last module. So that we will
                # check if it is 2 days older or more we don't need to send skip module email again.
                last_module_ora_submission_date = ''

                log.info("############## %s ##############", course.display_name)
                for index_chapter, chapter in enumerate(all_chapters):

                    # We introduced this boolean to check the count of graded sub-section in the module.
                    # We only need to send email if graded sub-section count is greater than or equall to 1.
                    graded_subsection = 0

                    # Getting sub-section in chapter
                    sequentials = modulestore().get_item(chapter)
                    log.info("$$$$$$$$$$$$$$$ %s $$$$$$$$$$$$$$$", sequentials.display_name)
                    for sequential in sequentials.children:
                        if course_blocks[str(sequential)]['graded']:

                            # We introduced this boolean to check if there is atleast
                            # one ora submitted in last 24 hours.
                            atleast_one_ora_submitted = False

                            graded_subsection += 1

                            # Getting verticals in sub-section
                            verticals = modulestore().get_item(sequential)

                            # Getting list of all ORAs in vertical of graded sub-section. We won't proceed if
                            # there are no ORAs in this vertical. There may be multiple vertical in sub-section
                            ora_list = get_ora_list(verticals)
                            if ora_list:
                                log.info("&&&&&&&&&&&&&&& %s &&&&&&&&&&&&&&&", verticals.display_name)
                                for ora_block in ora_list:
                                    response_submissions = Submission.objects.filter(
                                        student_item__student_id=anonymous_user.anonymous_user_id,
                                        student_item__item_id=ora_block
                                    ).first()
                                    if response_submissions:
                                        if index_chapter == last_chapter_index:
                                            last_module_ora_submission_date = response_submissions.created_at.date()
                                        # Response submitted date must be within last
                                        # 24 hours and we are checking that below
                                        if today - timedelta(hours=HOURS_TO_WAIT_FOR_EMAIL) <= \
                                                response_submissions.created_at.date() <= today:
                                            atleast_one_ora_submitted = True
                                            log.info('Response Created at: %s', response_submissions.created_at.date())
                                    else:
                                        log.error("ORA response not submitted")
                                        chapters_skipped.update({index_chapter: sequentials.display_name})
                                        break
                                else:
                                    # We don't want to send email for last module so check if user's current module
                                    # is less than total number of modules, number of graded sub-section is
                                    # greater than 0 and atleast one ora sub mitted in last 24 hours.
                                    if index_chapter != last_chapter_index and \
                                            graded_subsection > 0 and atleast_one_ora_submitted:
                                        send_weekly_email(user, course, str(chapter), course_blocks, index_chapter + 1)

                                    # We need to send skip email if user has completed last
                                    # module but has skipped one or more prevedxious module.
                                    elif index_chapter == last_chapter_index and bool(chapters_skipped):
                                        days_last_module_submission = today - last_module_ora_submission_date

                                        # We only need to send this email for once so we are checking if the
                                        # last module ora assessment is done in last 24 hours or not.
                                        if days_last_module_submission.days < 2:
                                            send_module_skip_email(user, course, chapters_skipped)
                                    continue
                                break


def send_weekly_email(user, course, chapter_block, all_course_blocks, next_chapter_index):
    """
        Send weekly emails for completed module

        Parameters:
        user: user, whom we are sending emails.
        course: Course for which we want to send email.
        chapter_block: XBlock info of Chapter block.
        all_course_blocks: Complete list of blocks in a course.
        next_chapter_index: next chapter index which url we will be sending to user.

        """
    current_chapter_name = all_course_blocks[chapter_block]['display_name']
    next_chapter_url = get_nth_chapter_link(course, chapter_index=next_chapter_index)
    context = {
        'emailId': HubSpotClient.ON_DEMAND_COURSE_WEEKLY_MODULE_COMPLETE,
        'message': {
            'to': user.email
        },
        'customProperties': {
            'first_name': user.first_name,
            'course_name': course.display_name,
            'module_title': current_chapter_name,
            'next_module_url': next_chapter_url,
            'email_address': user.email,
            'unsubscribe_link': get_my_account_link(course.id)
        }
    }

    task_send_hubspot_email.delay(context)
    log.info("Emailing to %s Task Completed for module completion", user.email)


def send_module_skip_email(user, course, chapters_skipped):
    """
        Send skip module emails after completing final module

        Parameters:
        user: user, whom we are sending emails.
        course: Course for which we want to send email.
        chapters_skipped: dict that are storing skipped chapter.

    """
    skip_module_url = get_nth_chapter_link(course, chapter_index=chapters_skipped.keys()[0])
    context = {
        'emailId': HubSpotClient.ON_DEMAND_WEEKLY_MODULE_SKIPPED_TEMPLATE,
        'message': {
            'to': user.email
        },
        'customProperties': {
            'first_name': user.first_name,
            'course_name': course.display_name,
            'module_list': get_module_list(chapters_skipped.values()),
            'email_address': user.email,
            'course_url': skip_module_url
        }
    }

    task_send_hubspot_email.delay(context)
    log.info("Emailing to %s Task Completed for skip module", user.email)


def get_module_list(chapter_names):
    """
    Get modules list in a custom string format
    """
    chapters_text = ''
    for chapter in chapter_names:
        module_text = ON_DEMAND_MODULE_TEXT_FOMATTER.format(
            module_name=chapter,
        )
        chapters_text = chapters_text + module_text
    return chapters_text


def get_ora_list(verticals):
    """
    Get all ORAs in a list from given vertical
    """
    oras = []
    for vertical in verticals.children:
        vertical_blocks = modulestore().get_item(vertical)
        for k, v in enumerate(vertical_blocks.children):
            if v.block_type == ORA_ASSESSMENT_BLOCK:
                oras.append(vertical_blocks.children[k])
    return oras
