"""
All helpers for openassessment
"""
import hashlib
from datetime import datetime, timedelta
from logging import getLogger

from django.conf import settings
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from pytz import utc
from submissions.models import Submission

from openassessment.assessment.api.staff import STAFF_TYPE
from openassessment.assessment.models import Assessment, AssessmentPart
from openassessment.assessment.serializers import rubric_from_dict
from openassessment.workflow.models import AssessmentWorkflow
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.url_utils import unquote_slashes
from xmodule.modulestore.django import modulestore

from .constants import DAYS_TO_WAIT_AUTO_ASSESSMENT, ORA_BLOCK_TYPE

log = getLogger(__name__)


def find_and_autoscore_submissions(enrollments, workflows_uuids):
    """
    Find ORA submissions corresponding to provided enrollments and workflow uuids. Autoscore all resulting submissions.
    :param (list) enrollments: All active CourseEnrollment objects for all self paced courses
    :param (list) workflows_uuids: All AssessmentWorkflow uuids for submissions excluding done and cancelled
    :return: None
    """
    days_to_wait = get_ora_days_to_wait_from_site_configurations()
    delta_date = datetime.now(utc).date() - timedelta(days=days_to_wait)
    all_submissions = []

    for enrollment in enrollments:
        list_of_submissions_to_autoscore = _get_submissions_to_autoscore_by_enrollment(
            enrollment=enrollment,
            workflows_uuids=workflows_uuids,
            delta_date=delta_date
        )
        if list_of_submissions_to_autoscore:
            all_submissions.extend(list_of_submissions_to_autoscore)

    _log_multiple_submissions_info(all_submissions, days_to_wait, delta_date)

    for submission in all_submissions:
        autoscore_ora_submission(submission=submission)


def get_ora_days_to_wait_from_site_configurations():
    """
    This function returns the maximum number of day to wait in-order to auto score ora. This value is fetched from
    site configuration, with a hardcoded default value from constants.
    """
    return configuration_helpers.get_value(
        'DAYS_TO_WAIT_AUTO_ASSESSMENT',
        DAYS_TO_WAIT_AUTO_ASSESSMENT
    )


def _get_submissions_to_autoscore_by_enrollment(enrollment, workflows_uuids, delta_date):
    """
    Find ORA submissions, for a specific enrollment, which correspond to provided workflow uuids.
    :param (CourseEnrollment) enrollment: Course enrollment to find submissions from
    :param (list) workflows_uuids: All AssessmentWorkflow uuids for submissions excluding done and cancelled
    :param (Date) delta_date: Find submissions before this date
    :return: All submissions in enrollment matching criteria
    :rtype: list
    """
    course_id = enrollment.course_id
    anonymous_user_id = enrollment.user.anonymoususerid_set.get(course_id=course_id).anonymous_user_id
    submissions = []

    all_ora_in_enrolled_course = modulestore().get_items(
        course_id,
        qualifiers={'category': ORA_BLOCK_TYPE}
    )

    for open_assessment in all_ora_in_enrolled_course:

        submission = Submission.objects.filter(
            student_item__student_id=anonymous_user_id,
            student_item__item_id=open_assessment.location,
            status=Submission.ACTIVE,
            created_at__date__lt=delta_date,
            uuid__in=list(workflows_uuids)
        ).order_by('-created_at').first()

        if submission:
            submissions.append(submission)

    return submissions


def _log_multiple_submissions_info(all_submissions, days_to_wait, delta_date):
    """
    Log ORA auto scoring status
    """
    if all_submissions:
        log.info('Autoscoring {count} submission(s)'.format(count=len(all_submissions)))
    else:
        log.info('No pending open assessment found to autoscore, since last {days} days, from {since_date}'.format(
            days=days_to_wait, since_date=delta_date, )
        )


def autoscore_ora_submission(submission):
    """
    Auto score ORA submission, by Philu bot. Score will appear as awarded by staff (instructor). This function will
    also mark all requirements of submitter to fulfilled, which means all ORA steps will be marked as completed.
    :param (Submission) submission: ORA submission model object
    :return: None
    """
    anonymous_user_id = submission.student_item.student_id
    usage_key = submission.student_item.item_id
    course_id_str = submission.student_item.course_id
    course_id = CourseKey.from_string(course_id_str)

    log.info('Started autoscoring submission {uuid} for course {course}'.format(
        uuid=submission.uuid, course=course_id_str)
    )

    # Find the associated rubric for that course_id & item_id
    rubric_dict = get_rubric_for_course(course_id, usage_key)

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
    # Rest previous score and auto score ORA as per assessment made by philu bot and selected options
    assessment_workflow = AssessmentWorkflow.objects.get(submission_uuid=submission.uuid)
    assessment_workflow.update_from_assessments(assessment_requirements=None, override_submitter_requirements=True)


def autoscore_ora(course_id, usage_key, student):
    """
    This function is a wrapper function for `autoscore_ora_submission`. It is only used by edx-ora2 command
    `autoscore_learners` command.
    :param (string) course_id: Course id
    :param (string) usage_key: Key for openassessment xBlock
    :param (dict) student: A dictionary with anonymous user id
    :return: None
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
        log.warn(u"No submission found for user {user_id}".format(user_id=anonymous_user_id))
        return
    autoscore_ora_submission(submission)


def select_options(rubric_dict):
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


def get_rubric_for_course(course_id, usage_key):
    course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id.to_deprecated_string())
    usage_key = course_id.make_usage_key_from_deprecated_string(unquote_slashes(usage_key))

    instance = modulestore().get_item(usage_key)
    return {
        'prompts': instance.prompts,
        'criteria': instance.rubric_criteria
    }


def get_philu_bot():
    # Check if bot user exist
    philu_bot, _ = User.objects.get_or_create(
        username='philubot',
        defaults={
            'first_name': 'PhilU',
            'last_name': 'Bot',
            'email': 'bot@philanthropyu.org',
            'is_active': True
        }
    )

    # Create anonymized id for the bot
    hasher = hashlib.md5()
    hasher.update(settings.SECRET_KEY)
    hasher.update(unicode(philu_bot.id))
    digest = hasher.hexdigest()

    return digest
