"""
Signal handler for enabling/disabling self-generated certificates based on the course-pacing.
"""


import logging

import six
from django.db.models.signals import post_save
from django.dispatch import receiver

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.certificates.models import (
    CertificateGenerationCourseSetting,
    CertificateStatuses,
    CertificateWhitelist,
    GeneratedCertificate
)
from lms.djangoapps.certificates.tasks import generate_certificate
from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.djangoapps.certificates.api import auto_certificate_generation_enabled
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.course_overviews.signals import COURSE_PACING_CHANGED
from openedx.core.djangoapps.signals.signals import (
    COURSE_GRADE_NOW_FAILED,
    COURSE_GRADE_NOW_PASSED,
    LEARNER_NOW_VERIFIED
)
from common.djangoapps.student.models import CourseEnrollment

log = logging.getLogger(__name__)
CERTIFICATE_DELAY_SECONDS = 2


@receiver(COURSE_PACING_CHANGED, dispatch_uid="update_cert_settings_on_pacing_change")
def _update_cert_settings_on_pacing_change(sender, updated_course_overview, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that course pacing has changed and enable/disable
    the self-generated certificates according to course-pacing.
    """
    CertificateGenerationCourseSetting.set_self_generatation_enabled_for_course(
        updated_course_overview.id,
        updated_course_overview.self_paced,
    )
    log.info(u'Certificate Generation Setting Toggled for {course_id} via pacing change'.format(
        course_id=updated_course_overview.id
    ))


@receiver(post_save, sender=CertificateWhitelist, dispatch_uid="append_certificate_whitelist")
def _listen_for_certificate_whitelist_append(sender, instance, **kwargs):  # pylint: disable=unused-argument
    course = CourseOverview.get_from_id(instance.course_id)
    if not auto_certificate_generation_enabled():
        return

    fire_ungenerated_certificate_task(instance.user, instance.course_id)
    log.info(u'Certificate generation task initiated for {user} : {course} via whitelist'.format(
        user=instance.user.id,
        course=instance.course_id
    ))


@receiver(COURSE_GRADE_NOW_PASSED, dispatch_uid="new_passing_learner")
def listen_for_passing_grade(sender, user, course_id, **kwargs):  # pylint: disable=unused-argument
    """
    Listen for a learner passing a course, send cert generation task,
    downstream signal from COURSE_GRADE_CHANGED
    """
    course = CourseOverview.get_from_id(course_id)
    if not auto_certificate_generation_enabled():
        return

    if fire_ungenerated_certificate_task(user, course_id):
        log.info(u'Certificate generation task initiated for {user} : {course} via passing grade'.format(
            user=user.id,
            course=course_id
        ))


@receiver(COURSE_GRADE_NOW_FAILED, dispatch_uid="new_failing_learner")
def _listen_for_failing_grade(sender, user, course_id, grade, **kwargs):  # pylint: disable=unused-argument
    """
    Listen for a learner failing a course, mark the cert as notpassing
    if it is currently passing,
    downstream signal from COURSE_GRADE_CHANGED
    """
    cert = GeneratedCertificate.certificate_for_student(user, course_id)
    if cert is not None:
        if CertificateStatuses.is_passing_status(cert.status):
            cert.mark_notpassing(grade.percent)
            log.info(u'Certificate marked not passing for {user} : {course} via failing grade: {grade}'.format(
                user=user.id,
                course=course_id,
                grade=grade
            ))


@receiver(LEARNER_NOW_VERIFIED, dispatch_uid="learner_track_changed")
def _listen_for_id_verification_status_changed(sender, user, **kwargs):  # pylint: disable=unused-argument
    """
    Catches a track change signal, determines user status,
    calls fire_ungenerated_certificate_task for passing grades
    """
    if not auto_certificate_generation_enabled():
        return

    user_enrollments = CourseEnrollment.enrollments_for_user(user=user)

    grade_factory = CourseGradeFactory()
    expected_verification_status = IDVerificationService.user_status(user)
    expected_verification_status = expected_verification_status['status']
    for enrollment in user_enrollments:
        if grade_factory.read(user=user, course=enrollment.course_overview).passed:
            if fire_ungenerated_certificate_task(user, enrollment.course_id, expected_verification_status):
                message = (
                    u'Certificate generation task initiated for {user} : {course} via track change ' +
                    u'with verification status of {status}'
                )
                log.info(message.format(
                    user=user.id,
                    course=enrollment.course_id,
                    status=expected_verification_status
                ))


def fire_ungenerated_certificate_task(user, course_key, expected_verification_status=None):
    """
    Helper function to fire certificate generation task.
    Auto-generation of certificates is available for following course modes:
        1- VERIFIED
        2- CREDIT_MODE
        3- PROFESSIONAL
        4- NO_ID_PROFESSIONAL_MODE

    Certificate generation task is fired to either generate a certificate
    when there is no generated certificate for user in a particular course or
    update a certificate if it has 'unverified' status.

    Task is fired to attempt an update to a certificate
    with 'unverified' status as this method is called when a user is
    successfully verified, any certificate associated
    with such user can now be verified.

    NOTE: Purpose of restricting other course modes (HONOR and AUDIT) from auto-generation is to reduce
    traffic to workers.
    """

    message = u'Entered into Ungenerated Certificate task for {user} : {course}'
    log.info(message.format(user=user.id, course=course_key))

    allowed_enrollment_modes_list = [
        CourseMode.VERIFIED,
        CourseMode.CREDIT_MODE,
        CourseMode.PROFESSIONAL,
        CourseMode.NO_ID_PROFESSIONAL_MODE,
        CourseMode.MASTERS,
        CourseMode.EXECUTIVE_EDUCATION,
    ]
    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(user, course_key)
    cert = GeneratedCertificate.certificate_for_student(user, course_key)

    generate_learner_certificate = (
        enrollment_mode in allowed_enrollment_modes_list and (cert is None or cert.status == 'unverified')
    )

    if generate_learner_certificate:
        kwargs = {
            'student': six.text_type(user.id),
            'course_key': six.text_type(course_key)
        }
        if expected_verification_status:
            kwargs['expected_verification_status'] = six.text_type(expected_verification_status)
        generate_certificate.apply_async(countdown=CERTIFICATE_DELAY_SECONDS, kwargs=kwargs)
        return True

    message = u'Certificate Generation task failed for {user} : {course}'
    log.info(message.format(user=user.id, course=course_key))
