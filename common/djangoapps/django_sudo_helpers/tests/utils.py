"""
django_sudo_heplers.utils
"""
from django.conf import settings
import django.contrib.sessions.middleware
import sudo.middleware


DJANGO_SUDO_FEATURES_KEY = 'ENABLE_DJANGO_SUDO'
DJANGO_SUDO_FEATURE_ENABLED = (
    DJANGO_SUDO_FEATURES_KEY in settings.FEATURES and settings.FEATURES[DJANGO_SUDO_FEATURES_KEY]
)


def sudo_middleware_process_request(request):
    """
    Initialize the session and is_sudo on request object.
    """
    if settings.FEATURES.get('ENABLE_DJANGO_SUDO', False):
        session_middleware = django.contrib.sessions.middleware.SessionMiddleware()
        session_middleware.process_request(request)
        sudo_middleware = sudo.middleware.SudoMiddleware()
        sudo_middleware.process_request(request)
