from django.core.urlresolvers import reverse
from django.shortcuts import redirect


class RedirectMiddleware(object):

    user_info_survey_url = reverse('user_info')
    interests_survey_url = reverse('interests')
    organization_survey_url = reverse('organization')

    def process_request(self, request):
        if not request.user.is_anonymous():
            user = request.user

            try:
                user.user_info_survey
            except Exception:

                if self.user_info_survey_url == request.get_full_path():
                    return None

                return redirect(self.user_info_survey_url)

            try:
                user.interest_survey
            except Exception:

                if self.interests_survey_url == request.get_full_path():
                    return None

                return redirect(self.interests_survey_url)

            try:
                user.organization_survey
            except Exception:
                if self.organization_survey_url == request.get_full_path():
                    return None

                return redirect(self.organization_survey_url)

        return None
