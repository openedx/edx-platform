from django.dispatch import receiver
from openedx.core.djangoapps.signals.signals import COURSE_COMPLETED
from openedx.features.genplus_features.genplus_learning.models import UnitCompletion
from openedx.features.genplus_features.genplus_badges.events.completion import (
    unit_badge_check,
    program_badge_check
)


@receiver(COURSE_COMPLETED, sender=UnitCompletion)
def create_unit_badge(sender, user, course_key, **kwargs):
    unit_badge_check(user, course_key)


@receiver(COURSE_COMPLETED, sender=UnitCompletion)
def create_program_badge(sender, user, course_key, **kwargs):
    program_badge_check(user, course_key)
