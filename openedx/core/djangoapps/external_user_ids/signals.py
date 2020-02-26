"""
Signal Handlers for External User Ids to be created and maintainer
"""

from logging import getLogger

from django.db.models.signals import post_save
from django.dispatch import receiver

from openedx.core.djangoapps.catalog.utils import get_programs
from .models import ExternalId, ExternalIdType

LOGGER = getLogger(__name__)


@receiver(post_save, sender='student.CourseEnrollment')
def create_external_id_for_microbachelors_program(
    sender, instance, created, **kwargs  # pylint: disable=unused-argument
):
    """
    Watches for post_save signal for creates on the CourseEnrollment table.
    Generate an External ID if the Enrollment is in a MicroBachelors Program
    """
    if (
        created and
        instance.user and
        not ExternalId.user_has_external_id(
            user=instance.user,
            type_name=ExternalIdType.MICROBACHELORS_COACHING)
    ):
        mb_programs = [
            program for program in get_programs(course=instance.course_id)
            if program.get('type_attrs', None) and program['type_attrs']['coaching_supported']
        ]
        if mb_programs:
            ExternalId.add_new_user_id(
                user=instance.user,
                type_name=ExternalIdType.MICROBACHELORS_COACHING
            )
