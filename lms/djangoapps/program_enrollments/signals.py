"""
Signal handlers for program enrollments
"""
from __future__ import absolute_import

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from social_django.models import UserSocialAuth
from lms.djangoapps.program_enrollments.models import ProgramEnrollment
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.user_api.accounts.signals import USER_RETIRE_LMS_MISC
from student.models import CourseEnrollmentException
from third_party_auth.models import SAMLProviderConfig

logger = logging.getLogger(__name__)


@receiver(USER_RETIRE_LMS_MISC)
def _listen_for_lms_retire(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Listener for the USER_RETIRE_LMS_MISC signal, does user retirement
    """
    user = kwargs.get('user')
    ProgramEnrollment.retire_user(user.id)


@receiver(post_save, sender=UserSocialAuth)
def matriculate_learner(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """
    Post-save signal to update any waiting program enrollments with a user,
    and enroll the user in any waiting course enrollments.

    In most cases this will just short-circuit. Enrollments will only be updated
    for a SAML provider with a linked organization.
    """
    if not created:
        return

    try:
        user = instance.user
        provider_slug, external_user_key = instance.uid.split(':')
        authorizing_org = SAMLProviderConfig.objects.current_set().get(slug=provider_slug).organization

        if not authorizing_org:
            return
    except (AttributeError, ValueError):
        logger.info(u'Ignoring non-saml social auth entry for user=%s', user.id)
        return
    except SAMLProviderConfig.DoesNotExist:
        logger.warning(u'Got incoming social auth for provider=%s but no such provider exists', provider_slug)
        return
    except SAMLProviderConfig.MultipleObjectsReturned:
        logger.warning(
            u'Unable to activate waiting enrollments for user=%s.'
            u'  Multiple active SAML configurations found for slug=%s. Expected one.',
            user.id,
            provider_slug)
        return

    incomplete_enrollments = ProgramEnrollment.objects.filter(
        external_user_key=external_user_key,
        user=None,
    ).prefetch_related('program_course_enrollments')

    for enrollment in incomplete_enrollments:
        try:
            enrollment_org = get_programs(uuid=enrollment.program_uuid)['authoring_organizations'][0]
            if enrollment_org['key'] != authorizing_org.short_name:
                continue
        except (KeyError, TypeError):
            logger.warning(
                u'Failed to complete waiting enrollments for organization=%s.'
                u' No catalog programs with matching authoring_organization exist.',
                authorizing_org.short_name
            )
            continue

        enrollment.user = user
        enrollment.save()
        for program_course_enrollment in enrollment.program_course_enrollments.all():
            try:
                program_course_enrollment.enroll(user)
            except CourseEnrollmentException as e:
                logger.warning(
                    u'Failed to enroll user=%s with waiting program_course_enrollment=%s: %s',
                    user.id,
                    program_course_enrollment.id,
                    e,
                )
                raise e
