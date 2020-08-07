import hashlib
from datetime import datetime
from logging import getLogger

from django.conf import settings
from django.contrib.auth.models import User
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from openassessment.assessment.models import Assessment, AssessmentPart
from openassessment.assessment.serializers import rubric_from_dict
from openassessment.workflow.models import AssessmentWorkflow
from pytz import utc
from submissions.api import reset_score, set_score
from submissions.models import Submission

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.url_utils import unquote_slashes
from openedx.features.philu_utils.utils import get_anonymous_user
from xmodule.modulestore.django import modulestore

from .constants import (
    ASSESSMENT_WORKFLOW_WAITING_STATUS,
    DAYS_TO_WAIT_AUTO_ASSESSMENT,
    ORA_BLOCK_TYPE
)

log = getLogger(__name__)


def _log_multiple_submissions_info(submissions):
    if len(submissions) > 1:
        submission_ids = map(str, [submission.id for submission in submissions])

        log.info('Multiple submissions found having ids {ids} in can_auto_score_ora'.format(
            ids=','.join(submission_ids)
        ))


def can_auto_score_ora(enrollment, course, block, index_chapter):
    anonymous_user = get_anonymous_user(enrollment.user, course.id)
    if not anonymous_user:
        return False
    response_submissions = Submission.objects.filter(
        student_item__student_id=anonymous_user.anonymous_user_id,
        student_item__item_id=block
    ).order_by('submitted_at')
    _log_multiple_submissions_info(response_submissions)
    response_submission = response_submissions.first()
    if not response_submission:
        return False
    log.info('Submission with id {id} was created at: {created_date}'.format(
        id=response_submission.id,
        created_date=response_submission.created_at.date()
    ))
    today = datetime.now(utc).date()
    delta_days = today - enrollment.created.date()
    response_submission_delta = today - response_submission.created_at.date()

    module_access_days = delta_days.days - (index_chapter * 7)
    waiting_for_others_submission_exists = AssessmentWorkflow.objects.filter(
        status=ASSESSMENT_WORKFLOW_WAITING_STATUS,
        course_id=course.id,
        item_id=block,
        submission_uuid=response_submission.uuid
    ).exists()
    days_to_wait_auto_assessment = get_ora_days_to_wait_from_site_configurations()
    return (
        module_access_days >= days_to_wait_auto_assessment and
        response_submission_delta.days >= days_to_wait_auto_assessment and
        waiting_for_others_submission_exists
    )


def get_ora_days_to_wait_from_site_configurations():
    """
    This function returns the maximum number of day to wait in-order to auto score ora. This value is fetched from
    site configuration, with a hardcoded default value from constants.
    """
    return configuration_helpers.get_value(
        'DAYS_TO_WAIT_AUTO_ASSESSMENT',
        DAYS_TO_WAIT_AUTO_ASSESSMENT
    )


def autoscore_ora(course_id, usage_key, student):
    anonymous_user_id = student['anonymous_user_id']

    # Find the associated rubric for that course_id & item_id
    rubric_dict = get_rubric_for_course(course_id, usage_key)

    rubric = rubric_from_dict(rubric_dict)
    options_selected, earned, possible = select_options(rubric_dict)

    # Use usage key and student id to get the submission of the user.
    course_id_str = course_id.to_deprecated_string()
    submissions = Submission.objects.filter(
        student_item__course_id=course_id_str,
        student_item__student_id=anonymous_user_id,
        student_item__item_id=usage_key,
        student_item__item_type=ORA_BLOCK_TYPE
    ).order_by('submitted_at')
    _log_multiple_submissions_info(submissions)
    submission = submissions.first()
    if not submission:
        log.warn(u"No submission found for user {user_id}".format(user_id=anonymous_user_id))
        return

    # Create assessments
    assessment = Assessment.create(
        rubric=rubric,
        scorer_id=get_philu_bot(),
        submission_uuid=submission.uuid,
        score_type='ST'
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

    reset_score(
        student_id=anonymous_user_id,
        course_id=course_id_str,
        item_id=usage_key
    )

    set_score(
        submission_uuid=str(submission.uuid),
        points_earned=earned,
        points_possible=possible
    )


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
