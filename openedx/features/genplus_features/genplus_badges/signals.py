from django.dispatch import receiver
from django.db.models.signals import post_save
from openedx.core.djangoapps.signals.signals import COURSE_COMPLETED
from openedx.features.genplus_features.genplus_learning.models import UnitCompletion
from openedx.features.genplus_features.genplus.models import Activity
from openedx.features.genplus_features.genplus.constants import ActivityTypes
from openedx.features.genplus_features.genplus_badges.events.completion import (
    unit_badge_check,
    program_badge_check
)
from .models import BoosterBadgeAward


@receiver(COURSE_COMPLETED, sender=UnitCompletion)
def create_unit_badge(sender, user, course_key, **kwargs):
    unit_badge_check(user, course_key)


@receiver(COURSE_COMPLETED, sender=UnitCompletion)
def create_program_badge(sender, user, course_key, **kwargs):
    program_badge_check(user, course_key)


# capture activity on badge award
@receiver(post_save, sender=BoosterBadgeAward)
def create_activity_on_badge_award(sender, instance, created, **kwargs):
    if created:
        Activity.objects.create(
            actor=instance.awarded_by.gen_user.teacher,
            type=ActivityTypes.BADGE_AWARD,
            action_object=instance,
            target=instance.user.gen_user.student
        )
