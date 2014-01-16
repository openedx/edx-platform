""" Utility functions related to HTTP requests """
from django.conf import settings
from microsite_configuration.middleware import MicrositeConfiguration


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
