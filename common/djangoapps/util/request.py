""" Utility functions related to HTTP requests """
from django.conf import settings
from microsite_configuration.middleware import MicrositeConfiguration
from track.contexts import COURSE_REGEX


def safe_get_host(request):
    """
    Get the host name for this request, as safely as possible.

    If ALLOWED_HOSTS is properly set, this calls request.get_host;
    otherwise, this returns whatever settings.SITE_NAME is set to.

    This ensures we will never accept an untrusted value of get_host()
    """
    if isinstance(settings.ALLOWED_HOSTS, (list, tuple)) and '*' not in settings.ALLOWED_HOSTS:
        return request.get_host()
    else:
        return MicrositeConfiguration.get_microsite_configuration_value('site_domain', settings.SITE_NAME)


def course_id_from_url(url):
    """
    Extracts the course_id from the given `url`.
    """
    url = url or ''

    match = COURSE_REGEX.match(url)
    course_id = ''
    if match:
        course_id = match.group('course_id') or ''

    return course_id