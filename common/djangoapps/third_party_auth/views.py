"""
Extra views required for SSO
"""
import logging

from django.conf import settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseServerError, Http404, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

import social
from social.apps.django_app.views import complete
from social.apps.django_app.utils import load_strategy, load_backend
from social.utils import setting_name

from student.models import UserProfile
from student.views import compose_and_send_activation_email
from .models import SAMLConfiguration

URL_NAMESPACE = getattr(settings, setting_name('URL_NAMESPACE'), None) or 'social'
log = logging.getLogger(__name__)

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
    profile = UserProfile.objects.get(user=request.user)
    compose_and_send_activation_email(request.user, profile)
    return redirect(request.GET.get('next', 'dashboard'))

def saml_logout_view(request):
    """
    Terminate the Open edX learner's session.  This view is mapped to the
    SAML Single Logout (SLO) URL included in the metadata response payload.

    Note: The current implementation does not take OIDC sessions into account.  For a more
    robust implementation we should combine the workflow executed here with the LogoutView
    mechanism found in common/student/views.py ~L2650.
    """

    # Ensure SAML support is enabled for this Open edX installation
    if not SAMLConfiguration.is_enabled(request.site):
        message = "SAML session termination attempted for {0}, but SAML is not enabled.".format(
            request.site.name
        )
        log.error(message)

    # Ensure there is an authenticated user included in the request
    if not hasattr(request, "user") or not request.user.is_authenticated():
        message = "SAML session termination attempted for {0}, but no user was provided.".format(
            request.site.name
        )
        log.info(message)

    # If none of the guards were tripped, we are clear to terminate the learner's session
    if not message:

        # There is a system handler registered to perform logging on successful logouts.
        request.is_from_logout = True

        # Now perform the actual application session termination
        logout(request)

    # Instruct the browser to send the user back to the origination point
    redirect()


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
