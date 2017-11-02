"""
The middleware for on-boarding survey app.
"""
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from lms.djangoapps.onboarding_survey.models import (
    UserInfoSurvey, InterestsSurvey, OrganizationSurvey, OrganizationDetailSurvey
)
from lms.djangoapps.onboarding_survey.helpers import is_first_signup_in_org


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
    org_detail_survey_url = reverse('org_detail_survey')
    dashboard_url = reverse('dashboard')

    def is_user_info_survey_complete(self, user):
        try:
            user.user_info_survey
            return True
        except UserInfoSurvey.DoesNotExist:
            return False

    def is_interest_survey_complete(self, user):
        try:
            user.interest_survey
            return True
        except InterestsSurvey.DoesNotExist:
            return False

    def is_org_survey_complete(self, user):
        try:
            user.organization_survey
            return True
        except OrganizationSurvey.DoesNotExist:
            return False

    def is_org_detail_survey_complete(self, user):
        try:
            user.org_detail_survey
            return True
        except OrganizationDetailSurvey.DoesNotExist:
            return False

    def process_request(self, request):

        if request.is_ajax() or request.get_full_path() == '/logout':
            return None

        if not request.user.is_anonymous():
            user = request.user

            if user.is_superuser:
                return None

            extended_profile = user.extended_profile

            if request.get_full_path() == self.dashboard_url and extended_profile.is_survey_completed:
                return None

            if not self.is_user_info_survey_complete(user):
                if self.user_info_survey_url == request.get_full_path():
                    return None
                return redirect(self.user_info_survey_url)

            if not self.is_interest_survey_complete(user):
                if self.interests_survey_url == request.get_full_path()\
                        or self.user_info_survey_url == request.get_full_path():
                    return None
                return redirect(self.interests_survey_url)

            if is_first_signup_in_org(extended_profile.organization) or extended_profile.is_poc:
                if not self.is_org_survey_complete(user):
                    if is_first_signup_in_org(extended_profile.organization) or extended_profile.is_poc:
                        if self.organization_survey_url == request.get_full_path()\
                                or self.interests_survey_url == request.get_full_path()\
                                or self.user_info_survey_url == request.get_full_path():
                            return None

                        return redirect(self.organization_survey_url)
                    else:
                        if request.get_full_path() == self.user_info_survey_url:
                            return None
                        return redirect(self.dashboard_url)

                if not self.is_org_detail_survey_complete(user):
                    if is_first_signup_in_org(extended_profile.organization) or extended_profile.is_poc:
                        if self.org_detail_survey_url == request.get_full_path()\
                                or self.organization_survey_url == request.get_full_path()\
                                or self.interests_survey_url == request.get_full_path()\
                                or self.user_info_survey_url == request.get_full_path():
                            return None
                        return redirect(self.org_detail_survey_url)
                    else:
                        if request.get_full_path() == self.user_info_survey_url:
                            return None
                        return redirect(self.dashboard_url)

            return None
