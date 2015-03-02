"""
Certificates API
"""

import logging
from certificates.models import CertificateStatuses as cert_status, certificate_status_for_student
from certificates.queue import XQueueCertInterface

log = logging.getLogger("edx.certificate")


def generate_user_certificates(student, course):
    """
    It will add the add-cert request into the xqueue.

    Args:
        student (object):  user
        course (object): course

    Returns:
        returns status of generated certificate
    """
    xqueue = XQueueCertInterface()
    ret = xqueue.add_cert(student, course.id, course=course)
    log.info(
        (
            u"Added a certificate generation task to the XQueue "
            u"for student %s in course '%s'. "
            u"The new certificate status is '%s'."
        ),
        student.id,
        unicode(course.id),
        ret
    )
    return ret


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
        'is_generating': True if current_status['status'] in [cert_status.generating, cert_status.error] else False,
        'download_url': None
    }

    if current_status['status'] == cert_status.downloadable:
        response_data['is_downloadable'] = True
        response_data['download_url'] = current_status['download_url']

    return response_data
