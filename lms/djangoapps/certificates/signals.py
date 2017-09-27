"""
Signal handler for enabling/disabling self-generated certificates based on the course-pacing.
"""
import datetime
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
import pytz

from certificates.models import (
    CertificateWhitelist,
    GeneratedCertificate
)
from certificates.tasks import generate_certificate, send_passing_learner_message
from certificates.views.shipping_information import PHYSICAL_CERTIFICATE_EXPERIMENT_ID, \
    PHYSICAL_CERTIFICATE_EXPERIMENT_KEY
from experiments.models import ExperimentData, ExperimentKeyValue
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from openedx.core.djangoapps.certificates.api import auto_certificate_generation_enabled
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.signals.signals import COURSE_GRADE_NOW_PASSED, LEARNER_NOW_VERIFIED, COURSE_CERT_AWARDED
from student.models import CourseEnrollment


log = logging.getLogger(__name__)
CERTIFICATE_DELAY_SECONDS = 2


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
def _listen_for_passing_grade(sender, user, course_id, **kwargs):  # pylint: disable=unused-argument
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
    expected_verification_status, _ = SoftwareSecurePhotoVerification.user_status(user)
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
    Helper function to fire un-generated certificate tasks

    The 'mode_is_verified' query is copied from the GeneratedCertificate model,
    but is done here in an attempt to reduce traffic to the workers.
    If the learner is verified and their cert has the 'unverified' status,
    we regenerate the cert.
    """
    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(user, course_key)
    mode_is_verified = enrollment_mode in GeneratedCertificate.VERIFIED_CERTS_MODES
    cert = GeneratedCertificate.certificate_for_student(user, course_key)
    if mode_is_verified and (cert is None or cert.status == 'unverified'):
        kwargs = {
            'student': unicode(user.id),
            'course_key': unicode(course_key)
        }
        if expected_verification_status:
            kwargs['expected_verification_status'] = unicode(expected_verification_status)
        generate_certificate.apply_async(countdown=CERTIFICATE_DELAY_SECONDS, kwargs=kwargs)
        return True


@receiver(COURSE_CERT_AWARDED)
def handle_course_cert_awarded(sender, user, course_key, mode, status, **kwargs):  # pylint: disable=unused-argument
    log.warn('handle cert award')
    try:
        exp_data = ExperimentData.objects.get(
            user=user,
            experiment_id=PHYSICAL_CERTIFICATE_EXPERIMENT_ID,
            key='ship_cert_{0}'.format(str(course_key)),
        )
    except ExperimentData.DoesNotExist:
        return

    if exp_data.value != '1':
        return

    send_passing_learner_message.apply_async((user.id, str(course_key)), retry=False)


@receiver(post_save, sender=CourseEnrollment, dispatch_uid='check_verified_upgrade')
def create_schedule(sender, **kwargs):
    enrollment = kwargs['instance']

    try:
        exp_data = ExperimentData.objects.get(
            user=enrollment.user,
            experiment_id=PHYSICAL_CERTIFICATE_EXPERIMENT_ID,
            key='showed_interest_{0}'.format(str(enrollment.course_id)),
        )
    except ExperimentData.DoesNotExist:
        return

    if exp_data.value != '1':
        return

    if enrollment.mode not in GeneratedCertificate.VERIFIED_CERTS_MODES:
        return

    try:
        end_time_str = ExperimentKeyValue.objects.get(
            experiment_id=PHYSICAL_CERTIFICATE_EXPERIMENT_ID,
            key='end_time'
        )
    except ExperimentKeyValue.DoesNotExist:
        return

    end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    if datetime.datetime.now(pytz.utc) >= end_time:
        return

    ship_exp_data = ExperimentData.objects.get_or_create(
        user=enrollment.user,
        experiment_id=PHYSICAL_CERTIFICATE_EXPERIMENT_ID,
        key='ship_cert_{0}'.format(str(enrollment.course_id)),
        defaults={'value': '1'},
    )
    ship_exp_data.value = '1'
    ship_exp_data.save()
