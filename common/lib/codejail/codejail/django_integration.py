"""Django integration for codejail"""

from django.core.exceptions import MiddlewareNotUsed
from django.conf import settings

import codejail.jail_code


class ConfigureCodeJailMiddleware(object):
    """Middleware to configure codejail on startup."""

    def __init__(self):
        python_bin = settings.CODE_JAIL.get('python_bin')
        if python_bin:
            user = settings.CODE_JAIL['user']
            codejail.jail_code.configure("python", python_bin, user=user)
        raise MiddlewareNotUsed
