"""
The middleware for on-boarding survey app.
"""
from django.core.urlresolvers import reverse, resolve
from django.shortcuts import redirect

from lms.djangoapps.onboarding.models import UserExtendedProfile, RegistrationType


class RedirectMiddleware(object):
    """
    The redirect middleware for on-boarding survey app.

    This middle ensures that no user access anything other than
    the on-boarding surveys if these are not completed.

    It is also, vigilant of the fact that user can come back to
    already completed survey from an uncompleted survey. So, it allows
    this kind of request.
    """

    def _get_urls_to_redirect(self, type):
        if type == 1:
            urls_to_redirect = {survey: reverse(survey) for survey in UserExtendedProfile.SURVEYS_LIST}
        else:
            urls_to_redirect = {survey: reverse(survey) for survey in UserExtendedProfile.SURVEYS_LIST_V2}

        urls_to_redirect['dashboard'] = reverse('dashboard')
        return urls_to_redirect

    @staticmethod
    def skip_redirection(request, user):
        skip_redirect = False

        if request.is_ajax() or request.get_full_path() == '/logout' or user.is_superuser or \
            '/activate/' in request.get_full_path() or '/onboarding/admin_activate/' in request.get_full_path():
            skip_redirect = True

        return skip_redirect

    def process_request(self, request):

        if not request.user.is_anonymous():
            user = request.user
            user_reg_type = RegistrationType.objects.filter(user=request.user).first()
            reg_type = user_reg_type.choice if user_reg_type else 1
            urls_to_redirect = self._get_urls_to_redirect(reg_type)

            if RedirectMiddleware.skip_redirection(request, user):
                return None

            user_extended_profile = user.extended_profile

            if reg_type == 1:

                attended_surveys = user_extended_profile.attended_surveys()
                unattended_surveys = user_extended_profile.unattended_surveys(_type="list")

                if not unattended_surveys and not request.get_full_path() == '/myaccount/settings/' \
                        and user.email_preferences and user.email_preferences.opt_in is None:
                    return redirect('/myaccount/settings/')

                if not unattended_surveys:
                    return None

                current_view_accessed = resolve(request.get_full_path()).view_name

                if unattended_surveys and current_view_accessed in attended_surveys:
                    return None

                elif unattended_surveys and current_view_accessed not in attended_surveys:
                    next_survey_to_complete = unattended_surveys[0]
                    if not urls_to_redirect[next_survey_to_complete] == request.get_full_path():
                        return redirect(urls_to_redirect[next_survey_to_complete])

                    return None
            else:

                # these two checks have been introduced so that when user comes from nodebb,
                # user gets redirected to correct flow based on user type
                if request.path == reverse('update_account_settings') and request.method == 'GET':
                    return redirect(reverse('update_account'))

                if request.path == reverse('update_organization') and request.method == 'GET':
                    return redirect(reverse('update_organization_v2'))

                attended_surveys = user_extended_profile.attended_surveys_v2()
                unattended_surveys = user_extended_profile.unattended_surveys_v2(_type="list")

                if not unattended_surveys and not request.get_full_path() == '/user-account/settings/' \
                        and user.email_preferences and user.email_preferences.opt_in is None:
                    return redirect('/user-account/settings/')

                if not unattended_surveys:
                    return None

                current_view_accessed = resolve(request.get_full_path()).view_name

                if unattended_surveys and current_view_accessed in attended_surveys:
                    return None

                elif unattended_surveys and current_view_accessed not in attended_surveys:
                    next_survey_to_complete = unattended_surveys[0]
                    if not urls_to_redirect[next_survey_to_complete] == request.get_full_path():
                        return redirect(urls_to_redirect[next_survey_to_complete])

                    return None

        return None

