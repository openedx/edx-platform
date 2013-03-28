"""Django integration for codejail"""

from django.core.exceptions import MiddlewareNotUsed
from django.conf import settings

import codejail.jailpy


class ConfigureCodeJailMiddleware(object):
    """Middleware to configure codejail on startup."""

    def __init__(self):
        python_bin = settings.CODE_JAIL.get('python_bin')
        if python_bin:
            user = settings.CODE_JAIL['user']
            codejail.jailpy.configure(python_bin, user=user)
        raise MiddlewareNotUsed
