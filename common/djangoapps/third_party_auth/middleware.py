"""Middleware classes for third_party_auth."""

from social.apps.django_app.middleware import SocialAuthExceptionMiddleware
from social.apps.django_app.default.models import UserSocialAuth

from . import pipeline
from .models import UserDataSharingConsentAudit


class ExceptionMiddleware(SocialAuthExceptionMiddleware):
    """Custom middleware that handles conditional redirection."""

    def get_redirect_uri(self, request, exception):
        # Fall back to django settings's SOCIAL_AUTH_LOGIN_ERROR_URL.
        redirect_uri = super(ExceptionMiddleware, self).get_redirect_uri(request, exception)

        # Safe because it's already been validated by
        # pipeline.parse_query_params. If that pipeline step ever moves later
        # in the pipeline stack, we'd need to validate this value because it
        # would be an injection point for attacker data.
        auth_entry = request.session.get(pipeline.AUTH_ENTRY_KEY)

        # Check if we have an auth entry key we can use instead
        if auth_entry and auth_entry in pipeline.AUTH_DISPATCH_URLS:
            redirect_uri = pipeline.AUTH_DISPATCH_URLS[auth_entry]

        return redirect_uri


class ResetSessionIfPipelineBrokenMiddleware(object):
    """
    Middleware signs the user out if they need to provide data sharing consent,
    haven't, and left the TPA pipeline prematurely
    """
    def process_view(self, request, view_func, view_args, view_kwargs):  # pylint: disable=unused-argument
        """
        Conditionally sign out users who don't provide data sharing consent
        """
        allowed_module_prefixes = (
            'third_party_auth.',
            'social.',
            'student.',
            'student_account.',
            'openedx.core.user_api.'
        )
        view_module = view_func.__module__
        if any(view_module.startswith(module_name) for module_name in allowed_module_prefixes):
            return
        if not pipeline.active_provider_requires_data_sharing(request):
            return

        running_pipeline = pipeline.get(request)
        if running_pipeline:
            social = running_pipeline['kwargs'].get('social')
            if social:
                try:
                    consent_provided = social.data_sharing_consent_audit.enabled
                except UserDataSharingConsentAudit.DoesNotExist:
                    consent_provided = False
                except AttributeError:
                    try:
                        consent_provided = UserSocialAuth.objects.get(
                            uid=social.get('uid', '')
                        ).data_sharing_consent_audit.enabled
                    except UserSocialAuth.DoesNotExist:
                        consent_provided = False
                    except UserDataSharingConsentAudit.DoesNotExist:
                        consent_provided = False
                if not consent_provided:
                    request.session.flush()
