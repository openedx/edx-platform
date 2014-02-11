"""
Middleware for UserPreferences
"""

from django.utils.translation.trans_real import parse_accept_lang_header

from user_api.models import UserPreference, LANGUAGE_KEY


class UserPreferenceMiddleware(object):
    """
    Middleware for user preferences.

    Ensures that, once set, a user's preferences are reflected in the page
    whenever they are logged in.
    """

    def process_request(self, request):
        """
        If a user's UserPreference contains a language preference,
        stick that preference in the session.
        """

        query = UserPreference.objects.filter(user=request.user, key=LANGUAGE_KEY)
        if query.exists():
            # there should only be one result for query
            request.session['django_language'] = query[0].value
