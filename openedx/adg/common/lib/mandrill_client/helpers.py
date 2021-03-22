"""
Helper methods for mandrill_client
"""
from django.conf import settings

from openedx.core.djangoapps.user_api.models import UserPreference


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
