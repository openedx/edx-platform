"""
django_sudo_heplers.utils
"""
import django.contrib.sessions.middleware
import sudo.middleware


def sudo_middleware_process_request(request):
    """
    Initialize the session and is_sudo on request object.
    """
    session_middleware = django.contrib.sessions.middleware.SessionMiddleware()
    session_middleware.process_request(request)
    sudo_middleware = sudo.middleware.SudoMiddleware()
    sudo_middleware.process_request(request)
