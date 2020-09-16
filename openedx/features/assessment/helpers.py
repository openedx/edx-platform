"""
All helpers for openassessment
"""
import hashlib
from datetime import datetime, timedelta
from logging import getLogger

from django.conf import settings
from django.contrib.auth.models import User
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from pytz import utc
from submissions.models import Submission

from openassessment.assessment.api.staff import STAFF_TYPE
from openassessment.assessment.models import Assessment, AssessmentPart
from openassessment.assessment.serializers import rubric_from_dict
from openassessment.workflow.models import AssessmentWorkflow
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.url_utils import unquote_slashes
from openedx.features.philu_utils.utils import get_anonymous_user
from xmodule.modulestore.django import modulestore

from .constants import DAYS_TO_WAIT_AUTO_ASSESSMENT, NO_PENDING_ORA, ORA_BLOCK_TYPE

log = getLogger(__name__)


def find_and_autoscore_submissions(enrollments, submission_uuids):
    """
    Find ORA submissions corresponding to provided enrollments and submission uuids. Autoscore all resulting
    submissions.

    Args:
        enrollments (list): All active CourseEnrollment objects for all self paced courses
        submission_uuids (list): All AssessmentWorkflow uuids for submissions excluding done and cancelled

    Returns:
        None
    """
    days_to_wait = configuration_helpers.get_value('DAYS_TO_WAIT_AUTO_ASSESSMENT', DAYS_TO_WAIT_AUTO_ASSESSMENT)
    delta_datetime = datetime.now(utc) - timedelta(days=days_to_wait)
    submissions_to_autoscore = []

    for enrollment in enrollments:
        submissions_to_autoscore_by_enrollment = _get_submissions_to_autoscore_by_enrollment(
            enrollment=enrollment,
            submission_uuids=submission_uuids,
            delta_datetime=delta_datetime
        )
        if submissions_to_autoscore_by_enrollment:
            submissions_to_autoscore.extend(submissions_to_autoscore_by_enrollment)
            log.info('Found {count} submission(s) for course enrollment {id}'.format(
                count=len(submissions_to_autoscore_by_enrollment), id=enrollment.id)
            )

    _log_multiple_submissions_info(submissions_to_autoscore, days_to_wait, delta_datetime)

    for submission in submissions_to_autoscore:
        autoscore_ora_submission(submission=submission)


def _get_submissions_to_autoscore_by_enrollment(enrollment, submission_uuids, delta_datetime):
    """
    Find ORA submissions, for a specific enrollment, which correspond to provided submission uuids.

    Args:
        enrollment (CourseEnrollment): Course enrollment to find submissions from
        submission_uuids (list): All AssessmentWorkflow uuids for submissions excluding done and cancelled
        delta_datetime (DateTime): Find submissions before this date

    Returns:
        list: All submissions in enrollment matching criteria
    """
    course_id = enrollment.course_id
    anonymous_user = get_anonymous_user(enrollment.user, course_id)

    if not anonymous_user:
        # TODO If AnonymousUserId model have more than one anonymous user ids against a combination of user and course
        #  then do not auto score. Ideally AnonymousUserId must have a unique combination of user and course. This is a
        #  temporary fix to avoid crash.
        return

    anonymous_user_id = anonymous_user.anonymous_user_id
    submissions = []

    all_ora_in_enrolled_course = modulestore().get_items(
        course_id,
        qualifiers={'category': ORA_BLOCK_TYPE}
    )

    for open_assessment in all_ora_in_enrolled_course:

        submission = Submission.objects.filter(
            student_item__student_id=anonymous_user_id,
            student_item__item_id=unicode(open_assessment.location),
            status=Submission.ACTIVE,
            created_at__lt=delta_datetime,
            uuid__in=list(submission_uuids)
        ).order_by('-created_at').first()

        if submission:
            submissions.append(submission)

    return submissions


def _log_multiple_submissions_info(submissions_to_autoscore, days_to_wait, delta_datetime):
    """
    Log ORA auto scoring status

    Args:
        submissions_to_autoscore (list):  List of ORA submission
        days_to_wait (int): No of days to wait to autoscore ORA
        delta_datetime (DateTime): Submission to autoscore submissions before this date

    Returns:
        None
    """
    if submissions_to_autoscore:
        log.info('Autoscoring {count} submission(s)'.format(count=len(submissions_to_autoscore)))
    else:
        log.info(NO_PENDING_ORA.format(days=days_to_wait, since=delta_datetime))


def autoscore_ora_submission(submission):
    """
    Auto score ORA submission, by Philu bot. Score will appear as awarded by staff (instructor). This function will
    also mark all requirements of submitter to fulfilled, which means all ORA steps will be marked as completed.

    Args:
        submission (Submission): ORA submission model object

    Returns:
        None
    """
    anonymous_user_id = submission.student_item.student_id
    usage_key = submission.student_item.item_id
    course_id_str = submission.student_item.course_id

    log.info('Started autoscoring submission {uuid} for course {course}'.format(
        uuid=submission.uuid, course=course_id_str)
    )

    # Find the associated rubric
    rubric_dict = get_rubric_from_ora(course_id_str, usage_key)

    rubric = rubric_from_dict(rubric_dict)
    options_selected = select_options(rubric_dict)[0]

    # Create assessments
    assessment = Assessment.create(
        rubric=rubric,
        scorer_id=get_philu_bot(),
        submission_uuid=submission.uuid,
        score_type=STAFF_TYPE
    )
    AssessmentPart.create_from_option_names(
        assessment=assessment,
        selected=options_selected
    )

    log.info(
        u"Created assessment for user {user_id}, submission {submission}, "
        u"course {course_id}, item {item_id} with rubric {rubric} by PhilU Bot.".format(
            user_id=anonymous_user_id,
            submission=submission.uuid,
            course_id=course_id_str,
            item_id=usage_key,
            rubric=rubric.content_hash
        )
    )

    # Mark all requirement of submitter to fulfilled and update status to done,
    # Reset previous score and auto score ORA as per assessment made by philu bot and selected options
    assessment_workflow = AssessmentWorkflow.objects.get(submission_uuid=submission.uuid)
    assessment_workflow.update_from_assessments(assessment_requirements=None, override_submitter_requirements=True)


def autoscore_ora(course_id, usage_key, student):
    """
    This function is a wrapper function for `autoscore_ora_submission`. It is only used by edx-ora2 command
    `autoscore_learners` command.

    Args:
        course_id (string): Course id
        usage_key (string): Key for openassessment xBlock
        student (dict): A dictionary with anonymous user id

    Returns:
        None
    """
    anonymous_user_id = student['anonymous_user_id']
    course_id_str = course_id.to_deprecated_string()
    submissions = Submission.objects.filter(
        student_item__course_id=course_id_str,
        student_item__student_id=anonymous_user_id,
        student_item__item_id=usage_key,
        student_item__item_type=ORA_BLOCK_TYPE
    ).order_by('submitted_at')
    submission = submissions.first()
    if not submission:
        log.warn(u'No submission found for user {user_id}'.format(user_id=anonymous_user_id))
        return
    autoscore_ora_submission(submission)


def select_options(rubric_dict):
    """
    Auto calculate total possible points, earned points and auto select selected options.

    Args:
        rubric_dict (dict): A dict with prompts and rubric criteria

    Returns:
        tuple: selected options, points earned and points possible
    """
    criteria = rubric_dict['criteria']
    options_selected = {}
    points_earned = 0
    points_possible = 0

    for crit in criteria:
        options = crit['options']
        points = list(set([o['points'] for o in options]))

        if len(points) > 2:
            # 3 pt rubric
            pt = points[-2]
        else:
            # 2 pt rubric
            pt = points[-1]

        points_earned += pt
        points_possible += max(points)
        # Get a list of all options with the pt value.
        # Some rubrics have multiple options against a single point value.
        # for such cases we are using list here.
        options_selected[crit['name']] = [o['name'] for o in options if o['points'] == pt][0]

    return options_selected, points_earned, points_possible


def get_rubric_from_ora(course_id, usage_key):
    """
    Get rubric from ORA xblock

    Args:
        course_id (string): Course id.
        usage_key (string): UsageKey of the block.

    Returns:
        dict: A dict with prompts and rubric criteria
    """
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    usage_key = course_id.make_usage_key_from_deprecated_string(unquote_slashes(usage_key))
    instance = modulestore().get_item(usage_key)
    return {
        'prompts': instance.prompts,
        'criteria': instance.rubric_criteria
    }


def get_philu_bot():
    """
    Get or create user for Philu bot

    Returns:
        string: A hash as a scorer id for Philu bot
    """
    philu_bot, _ = User.objects.get_or_create(
        username='philubot',
        defaults={
            'first_name': 'PhilU',
            'last_name': 'Bot',
            'email': 'bot@philanthropyu.org',
            'is_active': True
        }
    )

    # Create anonymize id for the bot
    hash_lib = hashlib.md5()
    hash_lib.update(settings.SECRET_KEY)
    hash_lib.update(unicode(philu_bot.id))
    digest = hash_lib.hexdigest()

    return digest
