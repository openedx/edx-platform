"""
The middleware for on-boarding survey app.
"""
from django.core.urlresolvers import reverse
from django.shortcuts import redirect


class RedirectMiddleware(object):
    """
    The redirect middleware for on-boarding survey app.

    This middle ensures that no user access anything other than
    the on-boarding surveys if these are not completed.

    It is also, vigilant of the fact that user can come back to
    already completed survey from an uncompleted survey. So, it allows
    this kind of request.
    """
    user_info_survey_url = reverse('user_info')
    interests_survey_url = reverse('interests')
    organization_survey_url = reverse('organization')

    def process_request(self, request):

        if request.is_ajax() or request.get_full_path() == '/logout':
            return None

        if not request.user.is_anonymous():
            user = request.user

            if user.is_superuser:
                return None

            try:
                user.user_info_survey
            except Exception:

                if self.user_info_survey_url == request.get_full_path():
                    return None

                return redirect(self.user_info_survey_url)

            try:
                user.interest_survey
            except Exception:

                if self.interests_survey_url == request.get_full_path()\
                        or self.user_info_survey_url == request.get_full_path():
                    return None

                return redirect(self.interests_survey_url)

            try:
                user.organization_survey
            except Exception:
                if self.organization_survey_url == request.get_full_path()\
                        or self.interests_survey_url == request.get_full_path()\
                        or self.user_info_survey_url == request.get_full_path():
                    return None

                return redirect(self.organization_survey_url)

        return None
