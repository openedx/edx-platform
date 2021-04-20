"""
Helper methods for mandrill_client
"""
import logging

import mandrill
from django.conf import settings

from openedx.core.djangoapps.user_api.models import UserPreference

log = logging.getLogger(__name__)


def add_user_preferred_language_to_template_slug(template, email):
    """
    Modify template slug according to user preferred language

    Arguments:
        template (string): template slug
        email (string): Email address of user

    Returns:
        string: template slug
    """

    user_pref = UserPreference.objects.filter(user__email=email, key='pref-lang').first()
    user_lang = user_pref.value if user_pref else None

    if user_lang and user_lang != settings.LANGUAGE_CODE:
        return '{}-{}'.format(template, user_lang)

    return template


def mandrill_exception_handler_decorator(raise_exception):
    """
    Exception handler decorator for mandrill client
    """
    def mandrill_exception_handler(email_func):
        def exception_handler(*args, **kwargs):
            try:
                result = email_func(*args, **kwargs)
                log.info(result)
                return result
            except mandrill.Error as e:
                log.error(f'A mandrill error occurred: {e.__class__} - {e}')

                if raise_exception:
                    raise
        return exception_handler
    return mandrill_exception_handler
