"""Certificates API

This is a Python API for generating certificates asynchronously.
Other Django apps should use the API functions defined in this module
rather than importing Django models directly.
"""
import logging

from django.conf import settings
from django.core.urlresolvers import reverse

from eventtracking import tracker

from xmodule.modulestore.django import modulestore

from certificates.models import (
    CertificateStatuses,
    certificate_status_for_student,
    CertificateGenerationCourseSetting,
    CertificateGenerationConfiguration,
    ExampleCertificateSet
)
from certificates.queue import XQueueCertInterface


log = logging.getLogger("edx.certificate")


def generate_user_certificates(student, course_key, course=None, insecure=False, generation_mode='batch',
                               forced_grade=None):
    """
    It will add the add-cert request into the xqueue.

    A new record will be created to track the certificate
    generation task.  If an error occurs while adding the certificate
    to the queue, the task will have status 'error'. It also emits
    `edx.certificate.created` event for analytics.

    Args:
        student (User)
        course_key (CourseKey)

    Keyword Arguments:
        course (Course): Optionally provide the course object; if not provided
            it will be loaded.
        insecure - (Boolean)
        generation_mode - who has requested certificate generation. Its value should `batch`
        in case of django command and `self` if student initiated the request.
        forced_grade - a string indicating to replace grade parameter. if present grading
                       will be skipped.
    """
    xqueue = XQueueCertInterface()
    if insecure:
        xqueue.use_https = False
    generate_pdf = not has_html_certificates_enabled(course_key, course)
    status, cert = xqueue.add_cert(student, course_key,
                                   course=course,
                                   generate_pdf=generate_pdf,
                                   forced_grade=forced_grade)
    if status in [CertificateStatuses.generating, CertificateStatuses.downloadable]:
        emit_certificate_event('created', student, course_key, course, {
            'user_id': student.id,
            'course_id': unicode(course_key),
            'certificate_id': cert.verify_uuid,
            'enrollment_mode': cert.mode,
            'generation_mode': generation_mode
        })
    return status


def regenerate_user_certificates(student, course_key, course=None,
                                 forced_grade=None, template_file=None, insecure=False):
    """
    It will add the regen-cert request into the xqueue.

    A new record will be created to track the certificate
    generation task.  If an error occurs while adding the certificate
    to the queue, the task will have status 'error'.

    Args:
        student (User)
        course_key (CourseKey)

    Keyword Arguments:
        course (Course): Optionally provide the course object; if not provided
            it will be loaded.
        grade_value - The grade string, such as "Distinction"
        template_file - The template file used to render this certificate
        insecure - (Boolean)
    """
    xqueue = XQueueCertInterface()
    if insecure:
        xqueue.use_https = False

    generate_pdf = not has_html_certificates_enabled(course_key, course)
    return xqueue.regen_cert(student, course_key, course, forced_grade, template_file, generate_pdf)


def certificate_downloadable_status(student, course_key):
    """
    Check the student existing certificates against a given course.
    if status is not generating and not downloadable or error then user can view the generate button.

    Args:
        student (user object): logged-in user
        course_key (CourseKey): ID associated with the course

    Returns:
        Dict containing student passed status also download url for cert if available
    """
    current_status = certificate_status_for_student(student, course_key)

    # If the certificate status is an error user should view that status is "generating".
    # On the back-end, need to monitor those errors and re-submit the task.

    response_data = {
        'is_downloadable': False,
        'is_generating': True if current_status['status'] in [CertificateStatuses.generating,
                                                              CertificateStatuses.error] else False,
        'download_url': None
    }

    if current_status['status'] == CertificateStatuses.downloadable:
        response_data['is_downloadable'] = True
        response_data['download_url'] = current_status['download_url']

    return response_data


def set_cert_generation_enabled(course_key, is_enabled):
    """Enable or disable self-generated certificates for a course.

    There are two "switches" that control whether self-generated certificates
    are enabled for a course:

    1) Whether the self-generated certificates feature is enabled.
    2) Whether self-generated certificates have been enabled for this particular course.

    The second flag should be enabled *only* when someone has successfully
    generated example certificates for the course.  This helps avoid
    configuration errors (for example, not having a template configured
    for the course installed on the workers).  The UI for the instructor
    dashboard enforces this constraint.

    Arguments:
        course_key (CourseKey): The course identifier.

    Keyword Arguments:
        is_enabled (boolean): If provided, enable/disable self-generated
            certificates for this course.

    """
    CertificateGenerationCourseSetting.set_enabled_for_course(course_key, is_enabled)

    if is_enabled:
        log.info(u"Enabled self-generated certificates for course '%s'.", unicode(course_key))
    else:
        log.info(u"Disabled self-generated certificates for course '%s'.", unicode(course_key))


def cert_generation_enabled(course_key):
    """Check whether certificate generation is enabled for a course.

    There are two "switches" that control whether self-generated certificates
    are enabled for a course:

    1) Whether the self-generated certificates feature is enabled.
    2) Whether self-generated certificates have been enabled for this particular course.

    Certificates are enabled for a course only when both switches
    are set to True.

    Arguments:
        course_key (CourseKey): The course identifier.

    Returns:
        boolean: Whether self-generated certificates are enabled
            for the course.

    """
    return (
        CertificateGenerationConfiguration.current().enabled and
        CertificateGenerationCourseSetting.is_enabled_for_course(course_key)
    )


def generate_example_certificates(course_key):
    """Generate example certificates for a course.

    Example certificates are used to validate that certificates
    are configured correctly for the course.  Staff members can
    view the example certificates before enabling
    the self-generated certificates button for students.

    Several example certificates may be generated for a course.
    For example, if a course offers both verified and honor certificates,
    examples of both types of certificate will be generated.

    If an error occurs while starting the certificate generation
    job, the errors will be recorded in the database and
    can be retrieved using `example_certificate_status()`.

    Arguments:
        course_key (CourseKey): The course identifier.

    Returns:
        None

    """
    xqueue = XQueueCertInterface()
    for cert in ExampleCertificateSet.create_example_set(course_key):
        xqueue.add_example_cert(cert)


def has_html_certificates_enabled(course_key, course=None):
    """
    It determines if course has html certificates enabled
    """
    html_certificates_enabled = False
    if settings.FEATURES.get('CERTIFICATES_HTML_VIEW', False):
        course = course if course else modulestore().get_course(course_key, depth=0)
        if get_active_web_certificate(course) is not None:
            html_certificates_enabled = True
    return html_certificates_enabled


def example_certificates_status(course_key):
    """Check the status of example certificates for a course.

    This will check the *latest* example certificate task.
    This is generally what we care about in terms of enabling/disabling
    self-generated certificates for a course.

    Arguments:
        course_key (CourseKey): The course identifier.

    Returns:
        list

    Example Usage:

        >>> from certificates import api as certs_api
        >>> certs_api.example_certificate_status(course_key)
        [
            {
                'description': 'honor',
                'status': 'success',
                'download_url': 'http://www.example.com/abcd/honor_cert.pdf'
            },
            {
                'description': 'verified',
                'status': 'error',
                'error_reason': 'No template found!'
            }
        ]

    """
    return ExampleCertificateSet.latest_status(course_key)


# pylint: disable=no-member
def get_certificate_url(user_id, course_id, verify_uuid):
    """
    :return certificate url
    """
    if settings.FEATURES.get('CERTIFICATES_HTML_VIEW', False):
        return u'{url}'.format(
            url=reverse(
                'cert_html_view',
                kwargs=dict(user_id=str(user_id), course_id=unicode(course_id))
            )
        )
    return '{url}{uuid}'.format(url=settings.CERTIFICATES_STATIC_VERIFY_URL, uuid=verify_uuid)


def get_active_web_certificate(course, is_preview_mode=None):
    """
    Retrieves the active web certificate configuration for the specified course
    """
    certificates = getattr(course, 'certificates', '{}')
    configurations = certificates.get('certificates', [])
    for config in configurations:
        if config.get('is_active') or is_preview_mode:
            return config
    return None


def emit_certificate_event(event_name, user, course_id, course=None, event_data=None):
    """
    Emits certificate event.
    """
    event_name = '.'.join(['edx', 'certificate', event_name])
    if course is None:
        course = modulestore().get_course(course_id, depth=0)
    context = {
        'org_id': course.org,
        'course_id': unicode(course_id)
    }
    data = {
        'user_id': user.id,
        'course_id': unicode(course_id),
        'certificate_url': get_certificate_url(user.id, course_id, event_data['certificate_id'])
    }
    event_data = event_data or {}
    event_data.update(data)

    with tracker.get_tracker().context(event_name, context):
        tracker.emit(event_name, event_data)
