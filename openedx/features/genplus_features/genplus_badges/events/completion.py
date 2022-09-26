import logging

from django.conf import settings

from lms.djangoapps.badges.models import BadgeClass, CourseEventBadgesConfiguration
from lms.djangoapps.badges.utils import requires_badges_enabled
from xmodule.modulestore.django import modulestore
from openedx.features.genplus_features.genplus_learning.models import Unit

LOGGER = logging.getLogger(__name__)


def _get_unit_completion_badge(user, course_key):
    from common.djangoapps.student.models import CourseEnrollment
    enrollment = CourseEnrollment.objects.filter(
        user=user, course_id=course_key
    ).order_by('-is_active').first()
    if not enrollment:
        return None
    mode = enrollment.mode
    course = modulestore().get_course(course_key)

    if not course.issue_badges:
        return None

    badge_class = BadgeClass.objects.filter(
        issuing_component='genplus__unit',
        course_id=course_key
    )
    if badge_class.exists():
        return badge_class.first()
    return None


@requires_badges_enabled
def unit_badge_check(user, course_key):
    course = modulestore().get_course(course_key)
    if not course.issue_badges:
        LOGGER.info("Course is not configured to issue badges.")
        return
    badge_class = _get_unit_completion_badge(user, course_key)
    if not badge_class:
        LOGGER.info("BadgeClass not found.")
        return
    if badge_class.get_for_user(user):
        LOGGER.info("Completion badge already exists for this user on this course.")
        # Badge already exists. Skip.
        return

    evidence_url = settings.GENPLUS_FRONTEND_URL
    badge_class.award(user, evidence_url)


@requires_badges_enabled
def program_badge_check(user, course_key):
    unit = Unit.objects.filter(course__id=course_key).first()
    if not unit:
        return

    program = unit.program
    course_keys = program.units.all().values_list('course', flat=True)
    completions = user.unitcompletion_set.filter(
        is_complete=True,
        course_key__in=course_keys,
    )
    if course_keys.count() == completions.count():
        badge_class_qs = BadgeClass.objects.filter(
            slug=program.slug,
            issuing_component='genplus__program'
        )
        badge_class = badge_class_qs.first()
        if badge_class_qs.count() == 1 and not badge_class.get_for_user(user):
            evidence_url = settings.GENPLUS_FRONTEND_URL
            badge_class.award(user, evidence_url)
