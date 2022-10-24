"""
This module contains signals / handlers related to programs.
"""


import logging

from django.dispatch import receiver

from openedx.core.djangoapps.credentials.helpers import is_learner_records_enabled_for_org
from openedx.core.djangoapps.signals.signals import (
    COURSE_CERT_AWARDED,
    COURSE_CERT_CHANGED,
    COURSE_CERT_DATE_CHANGE,
    COURSE_CERT_REVOKED
)

LOGGER = logging.getLogger(__name__)


@receiver(COURSE_CERT_AWARDED)
def handle_course_cert_awarded(sender, user, course_key, mode, status, **kwargs):  # pylint: disable=unused-argument
    """
    If programs is enabled and a learner is awarded a course certificate,
    schedule a celery task to process any programs certificates for which
    the learner may now be eligible.

    Args:
        sender:
            class of the object instance that sent this signal
        user:
            django.contrib.auth.User - the user to whom a cert was awarded
        course_key:
            refers to the course run for which the cert was awarded
        mode:
            mode / certificate type, e.g. "verified"
        status:
            either "downloadable" or "generating"

    Returns:
        None

    """
    # Import here instead of top of file since this module gets imported before
    # the credentials app is loaded, resulting in a Django deprecation warning.
    from openedx.core.djangoapps.credentials.models import CredentialsApiConfig

    # Avoid scheduling new tasks if certification is disabled.
    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        return

    # schedule background task to process
    LOGGER.debug(
        'handling COURSE_CERT_AWARDED: username=%s, course_key=%s, mode=%s, status=%s',
        user,
        course_key,
        mode,
        status,
    )
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from openedx.core.djangoapps.programs.tasks import award_program_certificates
    award_program_certificates.delay(user.username)


@receiver(COURSE_CERT_CHANGED)
def handle_course_cert_changed(sender, user, course_key, mode, status, **kwargs):
    """
        If a learner is awarded a course certificate,
        schedule a celery task to process that course certificate

        Args:
            sender:
                class of the object instance that sent this signal
            user:
                django.contrib.auth.User - the user to whom a cert was awarded
            course_key:
                refers to the course run for which the cert was awarded
            mode:
                mode / certificate type, e.g. "verified"
            status:
                "downloadable"

        Returns:
            None
    """
    # Import here instead of top of file since this module gets imported before
    # the credentials app is loaded, resulting in a Django deprecation warning.
    from openedx.core.djangoapps.credentials.models import CredentialsApiConfig

    verbose = kwargs.get('verbose', False)
    if verbose:
        msg = "Starting handle_course_cert_changed with params: "\
            "sender [{sender}], "\
            "user [{username}], "\
            "course_key [{course_key}], "\
            "mode [{mode}], "\
            "status [{status}], "\
            "kwargs [{kw}]"\
            .format(
                sender=sender,
                username=getattr(user, 'username', None),
                course_key=str(course_key),
                mode=mode,
                status=status,
                kw=kwargs
            )

        LOGGER.info(msg)

    # Avoid scheduling new tasks if certification is disabled.
    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        if verbose:
            LOGGER.info("Skipping send cert: is_learner_issuance_enabled False")
        return

    # Avoid scheduling new tasks if learner records are disabled for this site (right now, course certs are only
    # used for learner records -- when that changes, we can remove this bit and always send course certs).
    if not is_learner_records_enabled_for_org(course_key.org):
        if verbose:
            LOGGER.info(
                "Skipping send cert: ENABLE_LEARNER_RECORDS False for org [{org}]".format(
                    org=course_key.org
                )
            )
        return

    # schedule background task to process
    LOGGER.debug(
        'handling COURSE_CERT_CHANGED: username=%s, course_key=%s, mode=%s, status=%s',
        user,
        course_key,
        mode,
        status,
    )
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from openedx.core.djangoapps.programs.tasks import award_course_certificate
    award_course_certificate.delay(user.username, str(course_key))


@receiver(COURSE_CERT_REVOKED)
def handle_course_cert_revoked(sender, user, course_key, mode, status, **kwargs):  # pylint: disable=unused-argument
    """
    If programs is enabled and a learner's course certificate is revoked,
    schedule a celery task to revoke any related program certificates.

    Args:
        sender:
            class of the object instance that sent this signal
        user:
            django.contrib.auth.User - the user for which a cert was revoked
        course_key:
            refers to the course run for which the cert was revoked
        mode:
            mode / certificate type, e.g. "verified"
        status:
            revoked

    Returns:
        None

    """
    # Import here instead of top of file since this module gets imported before
    # the credentials app is loaded, resulting in a Django deprecation warning.
    from openedx.core.djangoapps.credentials.models import CredentialsApiConfig

    # Avoid scheduling new tasks if certification is disabled.
    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        return

    # schedule background task to process
    LOGGER.info(
        f"handling COURSE_CERT_REVOKED: user={user.id}, course_key={course_key}, mode={mode}, status={status}"
    )
    # import here, because signal is registered at startup, but items in tasks are not yet able to be loaded
    from openedx.core.djangoapps.programs.tasks import revoke_program_certificates
    revoke_program_certificates.delay(user.username, str(course_key))


@receiver(COURSE_CERT_DATE_CHANGE, dispatch_uid='course_certificate_date_change_handler')
def handle_course_cert_date_change(sender, course_key, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
    """
    If a course-run's `certificate_available_date` is updated, schedule a celery task to update the `visible_date`
    attribute of all (course) credentials awarded in the Credentials service.

    Args:
        course_key(CourseLocator): refers to the course whose certificate_available_date was updated.
    """
    # Import here instead of top of file since this module gets imported before the credentials app is loaded, resulting
    # in a Django deprecation warning.
    from openedx.core.djangoapps.credentials.models import CredentialsApiConfig

    # Avoid scheduling new tasks if we're not using the Credentials IDA
    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        LOGGER.warning(
            f"Skipping handling of COURSE_CERT_DATE_CHANGE for course {course_key}. Use of the Credentials service is "
            "disabled."
        )
        return

    LOGGER.info(f"Handling COURSE_CERT_DATE_CHANGE for course {course_key}")
    # import here, because signal is registered at startup, but items in tasks are not yet loaded
    from openedx.core.djangoapps.programs.tasks import update_certificate_visible_date_on_course_update
    from openedx.core.djangoapps.programs.tasks import update_certificate_available_date_on_course_update
    # update the awarded credentials `visible_date` attribute in the Credentials service after a date update
    update_certificate_visible_date_on_course_update.delay(str(course_key))
    # update the (course) certificate configuration in the Credentials service after a date update
    update_certificate_available_date_on_course_update.delay(str(course_key))
