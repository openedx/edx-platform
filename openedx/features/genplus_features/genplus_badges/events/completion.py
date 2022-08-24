import logging

from django.conf import settings

from lms.djangoapps.badges.models import BadgeClass, CourseEventBadgesConfiguration
from lms.djangoapps.badges.utils import requires_badges_enabled
from xmodule.modulestore.django import modulestore

LOGGER = logging.getLogger(__name__)


def get_completion_badge(user, course_key):
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
    badge_class = get_completion_badge(user, course_key)
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
    config = CourseEventBadgesConfiguration.current().course_group_settings
    awards = []
    for slug, keys in config.items():
        if course_key in keys:
            completions = user.unitcompletion_set.filter(
                is_complete=True,
                course_key__in=keys,
            )
            if len(completions) == len(keys):
                awards.append(slug)

    for slug in awards:
        badge_class = BadgeClass.objects.filter(
            slug=slug,
            issuing_component='genplus__program'
        )
        if badge_class.count() == 1:
            badge_class = badge_class.first()
            if badge_class.get_for_user(user):
                continue
            evidence_url = settings.GENPLUS_FRONTEND_URL
            badge_class.award(user, evidence_url)
