"""django-sudo pipeline definitions."""

import re

from django.conf import settings
from social.pipeline import partial

from cms.urls import LIBRARY_KEY_PATTERN
from sudo.utils import grant_sudo_privileges
from third_party_auth.pipeline import AUTH_ENTRY_SUDO
from util.request import COURSE_REGEX


# pylint: disable=unused-argument


@partial.partial
def create_sudo_session(strategy, auth_entry, *args, **kwargs):
    """
    Grant sudo privileges if user is authenticated and auth_entry
    is equal to AUTH_ENTRY_SUDO.
    """
    request = strategy.request if strategy else None
    if auth_entry == AUTH_ENTRY_SUDO and request.user.is_authenticated():
        _region = None
        redirect_to = strategy.session_get('next', '')
        match = COURSE_REGEX.match(redirect_to)
        match_string = 'course_id'
        if not match:
            if redirect_to.startswith('/library/'):
                library_regex = re.compile(r'^.*?/library/{}'.format(LIBRARY_KEY_PATTERN))
                match = library_regex.match(redirect_to)
                match_string = 'library_key_string'
            else:
                # COURSE_REGEX will not work for studio
                course_regex = re.compile(r'^.*?/course_team/{}'.format(settings.COURSE_ID_PATTERN))
                match = course_regex.match(redirect_to)

        if match:
            _region = match.group(match_string)

        if not _region and '/admin' in redirect_to:
            _region = 'django_admin'

        grant_sudo_privileges(request, region=_region)
