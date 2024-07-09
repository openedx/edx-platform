"""
Common utility methods for Course info apis.
"""

from lms.djangoapps.certificates.api import certificate_downloadable_status


def get_user_certificate_download_url(request, user, course_id):
    """
    Return the information about the user's certificate in the course.

    Arguments:
        request (Request): The request object.
        user (User): The user object.
        course_id (str): The identifier of the course.
    Returns:
        (dict): A dict containing information about location of the user's certificate
        or an empty dictionary, if there is no certificate.
    """
    certificate_info = certificate_downloadable_status(user, course_id)
    if certificate_info['is_downloadable']:
        return {
            'url': request.build_absolute_uri(certificate_info['download_url']),
        }
    return {}
