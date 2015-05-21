"""
Common utility functions useful throughout the certificates
"""
# pylint: disable=no-member

from django.core.urlresolvers import reverse


def get_certificate_url(user_id, course_id):
    """
    :return certificate url
    """
    url = u'{url}'.format(url=reverse('cert_html_view',
                                      kwargs=dict(
                                          user_id=str(user_id),
                                          course_id=unicode(course_id))))
    return url
