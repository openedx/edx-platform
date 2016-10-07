"""
Extra views required for SSO
"""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseServerError, Http404, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
import social
from social.apps.django_app.views import complete
from social.apps.django_app.utils import load_strategy, load_backend
from social.utils import setting_name
from .models import SAMLConfiguration, UserDataSharingConsentAudit
from .pipeline import get as get_running_pipeline, get_complete_url
from .provider import Registry

URL_NAMESPACE = getattr(settings, setting_name('URL_NAMESPACE'), None) or 'social'


def inactive_user_view(request):
    """
    A newly or recently registered user has completed the social auth pipeline.
    Their account is not yet activated, but we let them login since the third party auth
    provider is trusted to vouch for them. See details in pipeline.py.

    The reason this view exists is that if we don't define this as the
    SOCIAL_AUTH_INACTIVE_USER_URL, inactive users will get sent to LOGIN_ERROR_URL, which we
    don't want.
    """
    # 'next' may be set to '/account/finish_auth/.../' if this user needs to be auto-enrolled
    # in a course. Otherwise, just redirect them to the dashboard, which displays a message
    # about activating their account.
    return redirect(request.GET.get('next', 'dashboard'))


def saml_metadata_view(request):
    """
    Get the Service Provider metadata for this edx-platform instance.
    You must send this XML to any Shibboleth Identity Provider that you wish to use.
    """
    if not SAMLConfiguration.is_enabled(request.site):
        raise Http404
    complete_url = reverse('social:complete', args=("tpa-saml", ))
    if settings.APPEND_SLASH and not complete_url.endswith('/'):
        complete_url = complete_url + '/'  # Required for consistency
    saml_backend = load_backend(load_strategy(request), "tpa-saml", redirect_uri=complete_url)
    metadata, errors = saml_backend.generate_metadata_xml()

    if not errors:
        return HttpResponse(content=metadata, content_type='text/xml')
    return HttpResponseServerError(content=', '.join(errors))


@csrf_exempt
@social.apps.django_app.utils.psa('{0}:complete'.format(URL_NAMESPACE))
def lti_login_and_complete_view(request, backend, *args, **kwargs):
    """This is a combination login/complete due to LTI being a one step login"""

    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')

    request.backend.start()
    return complete(request, backend, *args, **kwargs)


def post_to_custom_auth_form(request):
    """
    Redirect to a custom login/register page.

    Since we can't do a redirect-to-POST, this view is used to pass SSO data from
    the third_party_auth pipeline to a custom login/register form (possibly on another server).
    """
    pipeline_data = request.session.pop('tpa_custom_auth_entry_data', None)
    if not pipeline_data:
        raise Http404
    # Verify the format of pipeline_data:
    data = {
        'post_url': pipeline_data['post_url'],
        # data: The provider info and user's name, email, etc. as base64 encoded JSON
        # It's base64 encoded because it's signed cryptographically and we don't want whitespace
        # or ordering issues affecting the hash/signature.
        'data': pipeline_data['data'],
        # The cryptographic hash of user_data:
        'hmac': pipeline_data['hmac'],
    }
    return render(request, 'third_party_auth/post_custom_auth_entry.html', data)


class GrantDataSharingPermissions(View):
    """
    View handles the case in which we get to the "verify consent" step, but consent
    hasn't yet been provided - this view contains a GET view that provides a form for
    consent to be provided, and a POST view that consumes said form.
    """
    def get(self, request):
        """
        Render a form to collect user input about data sharing consent
        """
        running_pipeline = get_running_pipeline(request)
        if running_pipeline:
            current_provider = Registry.get_from_pipeline(running_pipeline)
            if current_provider:
                name = current_provider.name
            else:
                raise Http404
        else:
            raise Http404
        data = {'sso_provider': name}
        return render(request, 'third_party_auth/grant_data_sharing_permissions.html', data)

    def post(self, request):
        """
        Process the above form
        """
        running_pipeline = get_running_pipeline(request)
        if not running_pipeline:
            raise Http404
        consent_provided = request.POST.get('data_sharing_consent', False)
        social_auth = running_pipeline['kwargs']['social']
        try:
            consent = social_auth.data_sharing_consent_audit
        except UserDataSharingConsentAudit.DoesNotExist:
            consent = UserDataSharingConsentAudit.create(user_social_auth=social_auth)
        if consent_provided:
            consent.enable()
            consent.save()
            backend_name = running_pipeline['kwargs']['backend'].name
            return redirect(get_complete_url(backend_name))
        else:
            consent.disable()
            consent.save()
            request.session.flush()
            # Flush the session to avoid the possibility of accidental login and to abort the pipeline
            return redirect(reverse('dashboard'))
