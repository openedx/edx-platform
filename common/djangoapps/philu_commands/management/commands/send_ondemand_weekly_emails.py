import math
from pytz import utc
from datetime import datetime
from logging import getLogger

from django.core.management.base import BaseCommand

from submissions.models import Submission
from courseware.models import StudentModule
from common.lib.mandrill_client.client import MandrillClient
from student.models import CourseEnrollment, AnonymousUserId

from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.courseware.helpers import get_nth_chapter_link
from openedx.features.ondemand_email_preferences.helpers import get_my_account_link
from openedx.features.ondemand_email_preferences.models import OnDemandEmailPreferences

log = getLogger(__name__)

MINIMUM_MODULE_PROGRESS = 2
DAYS_TO_COMPLETE_ONE_MODULE = 7
today = datetime.now(utc).date()
UNGRADED_BLOCKS = ['Blank Common Problem', 'Blank Advanced Problem', 'audio', 'video', 'survey', 'word_cloud']
IGNORED_PROBLEMS = ['table', 'google-document', 'gp-v2-project', 'problem-builder']
BLOCKS_TYPES = {'html_type': 'html', 'problem_type': 'problem', 'drag_drop_type': 'drag-and-drop-v2',
                'ora_type': 'openassessment'}
EMAIL_SUBJECT_LINE = 'Get started on the next module of {course_name}'


class Command(BaseCommand):
    help = """
        Send weekly emails to those users who have completed the scheduled graded module. This email will not be sent 
        for those module which don't have at-least one graded sub-section.
    """

    def handle(self, *args, **options):

        courses = CourseOverview.objects.filter(self_paced=True)

        for course in courses:
            try:
                course_struct = CourseStructure.objects.get(course_id=course.id).structure
            except CourseStructure.DoesNotExist:
                log.error('Course doesn\'t have a proper structure.')
                raise

            course_blocks = course_struct['blocks']

            # If course doesn't have any blocks, continue.
            if not course_blocks:
                continue

            enrollments = CourseEnrollment.objects.filter(course_id=course.id, is_active=True)

            for enrollment in enrollments:
                delta_days = today - enrollment.created.date()

                # one is added to get user's current module.
                current_module = int(math.floor((delta_days.days / DAYS_TO_COMPLETE_ONE_MODULE)) + 1)
                user = enrollment.user

                # If user hasn't enable email preferences for on demand course, no need to go further.
                if not get_user_email_preferences(user, course.id):
                    continue

                log.info('User: %s ****** Current Module: %s', user, current_module)

                if current_module < MINIMUM_MODULE_PROGRESS:
                    log.info('Current module is less than %s', MINIMUM_MODULE_PROGRESS)
                    continue
                elif delta_days.days % DAYS_TO_COMPLETE_ONE_MODULE != 0:
                    log.info('%s days passed since module ended. We need to send this email just one time,'
                             ' right after module due date expires', delta_days.days % DAYS_TO_COMPLETE_ONE_MODULE)
                    continue
                else:
                    # Flag to check if section is completed or not. By default it will be True
                    is_section_complete = True
                    course_chapters = modulestore().get_items(
                        course.id,
                        qualifiers={'category': 'course'}
                    )
                    if not course_chapters:
                        log.info('%s Course don\'t have any chapters', course.display_name)
                        continue

                    # To maintain counter of graded sub section.
                    graded_subsections = 0

                    # We are subtracting 2 from current module, 1 for adjusting index as list indexs starts from 0 and
                    # current module starts from 1 and other 1 to get previous module.
                    try:
                        chapter = course_chapters[0].children[current_module - 2]
                    except IndexError:
                        log.info("Course modules are ended for %s", user)
                        continue
                    sequentials = modulestore().get_item(chapter)
                    for index_sequential, sequential in enumerate(sequentials.children):
                        if course_blocks[str(sequential)]['graded']:
                            graded_subsections += 1
                            verticals = modulestore().get_item(sequential)
                            for index_vertical, vertical in enumerate(verticals.children):
                                vertical_blocks = modulestore().get_item(vertical)
                                log.info("************************** %s ************************",
                                         vertical_blocks.display_name)
                                for index_block, block in enumerate(vertical_blocks.children):
                                    if block.block_type == BLOCKS_TYPES.get('html_type'):
                                        try:
                                            has_view_html(user, sequential)
                                        except:
                                            break
                                    elif block.block_type == BLOCKS_TYPES.get('problem_type') or \
                                            block.block_type == BLOCKS_TYPES.get('drag_drop_type'):
                                        try:
                                            problem = StudentModule.objects.get(student_id=user.id,
                                                                                module_state_key=block)
                                            if has_block_graded(course_blocks, str(block)):
                                                if problem.grade is not None and problem.max_grade is not None:
                                                    log.info("%s problem is solved", block)
                                                    continue
                                                else:
                                                    log.info("%s problem isn't solved", block)
                                                    break
                                            else:
                                                log.info("%s problem isn't graded", block)
                                                continue
                                        except StudentModule.DoesNotExist:
                                            log.error("Module entry don't exists in Student Module Table")
                                            break
                                    elif block.block_type == BLOCKS_TYPES.get('ora_type'):
                                        anonymous_user = get_anonymous_id(user, course.id)
                                        try:
                                            response_submissions = Submission.objects.get(
                                                student_item__student_id=anonymous_user.anonymous_user_id,
                                                student_item__item_id=block)
                                            log.info('Response Created at: %s',
                                                     response_submissions.created_at.date())
                                            log.info("%s problem is solved", block)
                                        except Submission.DoesNotExist:
                                            log.error("ORA response not submitted")
                                            break
                                    elif block.block_type in UNGRADED_BLOCKS:
                                        if has_block_graded(course_blocks, str(block)):
                                            try:
                                                StudentModule.objects.get(student_id=user.id,
                                                                          module_state_key=block)
                                                log.info("%s %s View By user", block, block.block_type)
                                            except StudentModule.DoesNotExist:
                                                log.error("%s not viewed yet", block.block_type)
                                                break
                                        else:
                                            log.error("%s isn't graded yet", block.block_type)
                                # This will break the vertical_blocks loop so that blocks in other verticals will be
                                # checked in case user hasn't attempted any graded block.
                                else:
                                    continue  # only executed if the inner loop did NOT break
                                # This flag suggests that there is some uncompleted graded blocks
                                #  so emails will not be sent in this case
                                is_section_complete = False
                                break
                            # This will break the sequentials loop so that other blocks will be checked in case user
                            # hasn't attempted any graded block.
                            else:
                                continue  # only executed if the inner loop did NOT break
                            break

                    # We don't want to send email for last module so check if user's current module is less than
                    # total number of modules.
                    if graded_subsections > 0 and \
                            (current_module - 1) < len(course_chapters[0].children) and is_section_complete:
                        send_weekly_email(user, course, str(chapter), course_blocks, current_module)


def has_block_graded(all_blocks, block):
    if all_blocks[block]['display_name'] in UNGRADED_BLOCKS:
        return False
    return all_blocks[block]['graded']


def has_view_html(user, block):
    try:
        StudentModule.objects.get(student_id=user.id, module_state_key=block)
        log.info("THis is HTML view component so user has visited this subsection")
    except StudentModule.DoesNotExist:
        log.info("%s hadn't visited this subsection", user)


def get_anonymous_id(user, course_id):
    try:
        anonymous_user = AnonymousUserId.objects.get(user=user, course_id=course_id)
    except AnonymousUserId.DoesNotExist:
        log.error('Anonymous Id doesn\'t exists for User: %s', user)
    except AnonymousUserId.MultipleObjectsReturned:
        log.error('Multiple Anonymous Ids for User: %s', user)
    return anonymous_user


def get_user_email_preferences(user, course_id):
    try:
        email_pref = OnDemandEmailPreferences.objects.get(user=user, course_id=course_id)
        return email_pref.is_enabled
    except OnDemandEmailPreferences.DoesNotExist:
        log.info("No email preferences found for %s hence considered True", user)
        return True


def send_weekly_email(user, course, chapter, all_blocks, current_module):
    current_chapter_name = all_blocks[chapter]['display_name']
    template = MandrillClient.ON_DEMAND_WEEKLY_MODULE_COMPLETE_TEMPLATE
    next_chapter_url = get_nth_chapter_link(course, chapter_index=current_module - 1)
    context = {
        'first_name': user.first_name,
        'course_name': course.display_name,
        'module_title': current_chapter_name,
        'next_module_url': next_chapter_url,
        'email_address': user.email,
        'unsubscribe_link': get_my_account_link(course.id)
    }

    subject = EMAIL_SUBJECT_LINE.format(course_name=course.display_name)

    MandrillClient().send_mail(template, user.email, context, subject=subject)
    log.info("Emailing to %s Task Completed", user.email)
