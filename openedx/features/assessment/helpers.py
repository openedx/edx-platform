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

from openedx.core.lib.url_utils import unquote_slashes
from openedx.features.philu_utils.utils import get_anonymous_user
from xmodule.modulestore.django import modulestore

from .constants import ASSESSMENT_WORKFLOW_WAITING_STATUS, DAYS_TO_WAIT_AUTO_ASSESSMENT

log = getLogger(__name__)


def can_auto_score_ora(enrollment, course, block, index_chapter):
    anonymous_user = get_anonymous_user(enrollment.user, course.id)
    if not anonymous_user:
        return False
    response_submission = Submission.objects.filter(
        student_item__student_id=anonymous_user.anonymous_user_id,
        student_item__item_id=block).first()
    if not response_submission:
        return False
    log.info('Response Created at: {created_date}'.format(
        created_date=response_submission.created_at.date()
    ))
    today = datetime.now(utc).date()
    delta_days = today - enrollment.created.date()
    response_submission_delta = today - response_submission.created_at.date()

    # check if this chapter is 2 weeks older or not.
    module_access_days = delta_days.days - (index_chapter * 7)
    waiting_for_others_submission_exists = AssessmentWorkflow.objects.filter(
        status=ASSESSMENT_WORKFLOW_WAITING_STATUS,
        course_id=course.id,
        item_id=block,
        submission_uuid=response_submission.uuid
    ).exists()
    return (
        module_access_days >= DAYS_TO_WAIT_AUTO_ASSESSMENT and
        response_submission_delta.days >= DAYS_TO_WAIT_AUTO_ASSESSMENT and
        waiting_for_others_submission_exists
    )


def autoscore_ora(course_id, usage_key, student):

    # Find the associated rubric for that course_id & item_id
    rubric_dict = get_rubric_for_course(course_id, usage_key)

    rubric = rubric_from_dict(rubric_dict)
    options_selected, earned, possible = select_options(rubric_dict)

    # Use usage key and student id to get the submission of the user.
    try:
        submission = Submission.objects.get(
            student_item__course_id=course_id.to_deprecated_string(),
            student_item__student_id=student['anonymous_user_id'],
            student_item__item_id=usage_key,
            student_item__item_type='openassessment'
        )
    except Submission.DoesNotExist:
        log.warn(u"No submission found for user {user_id}".format(
            user_id=student['anonymous_user_id']
        ))
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
            user_id=student['anonymous_user_id'],
            submission=submission.uuid,
            course_id=course_id.to_deprecated_string(),
            item_id=usage_key,
            rubric=rubric.content_hash
        )
    )

    reset_score(
        student_id=student['anonymous_user_id'],
        course_id=course_id.to_deprecated_string(),
        item_id=usage_key
    )

    set_score(
        submission_uuid=submission.uuid,
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
