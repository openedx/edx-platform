"""
Signal Handlers for External User Ids to be created and maintainer
"""

from logging import getLogger

from django.db.models.signals import post_save
from django.dispatch import receiver

from openedx.core.djangoapps.catalog.utils import get_programs

from .models import ExternalId, ExternalIdType

LOGGER = getLogger(__name__)


def _user_needs_external_id(instance, created):
    return (
        created and
        instance.user and
        not ExternalId.user_has_external_id(
            user=instance.user,
            type_name=ExternalIdType.MICROBACHELORS_COACHING)
    )


@receiver(post_save, sender='student.CourseEnrollment')
def create_external_id_for_microbachelors_program(
    sender, instance, created, **kwargs  # pylint: disable=unused-argument
):
    """
    Watches for post_save signal for creates on the CourseEnrollment table.
    Generate an External ID if the Enrollment is in a MicroBachelors Program
    """
    if _user_needs_external_id(instance, created):
        mb_programs = [
            program for program in get_programs(course=instance.course_id)
            if program.get('type_attrs', {}).get('coaching_supported')
        ]
        if mb_programs:
            ExternalId.add_new_user_id(
                user=instance.user,
                type_name=ExternalIdType.MICROBACHELORS_COACHING
            )


@receiver(post_save, sender='entitlements.CourseEntitlement')
def create_external_id_for_microbachelors_program_entitlement(
    sender, instance, created, **kwargs  # pylint: disable=unused-argument
):
    """
    Watches for post_save signal for creates on the CourseEntitlement table.
    Generate an External ID if the Entitlement is in a MicroBachelors Program
    """
    if _user_needs_external_id(instance, created):
        mb_programs = [
            program for program in get_programs(catalog_course_uuid=instance.course_uuid)
            if program.get('type_attrs', {}).get('coaching_supported')
        ]
        if mb_programs:
            ExternalId.add_new_user_id(
                user=instance.user,
                type_name=ExternalIdType.MICROBACHELORS_COACHING
            )
