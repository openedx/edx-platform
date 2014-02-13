"""
Middleware for UserPreferences
"""

from user_api.models import UserPreference, LANGUAGE_KEY


class UserPreferenceMiddleware(object):
    """
    Middleware for user preferences.

    Ensures that, once set, a user's preferences are reflected in the page
    whenever they are logged in.
    """

    def process_request(self, request):
        """
        If a user's UserPreference contains a language preference and there is
        no language set on the session (i.e. from dark language overrides), use the user's preference.
        """
        if request.user.is_authenticated() and 'django_language' not in request.session:
            user_pref = UserPreference.get_preference(request.user, LANGUAGE_KEY)
            if user_pref:
                request.session['django_language'] = user_pref
