"""Middleware classes for third_party_auth."""

from social.apps.django_app.middleware import SocialAuthExceptionMiddleware

from . import pipeline


class ExceptionMiddleware(SocialAuthExceptionMiddleware):
    """Custom middleware that handles conditional redirection."""

    def get_redirect_uri(self, request, exception):
        # Safe because it's already been validated by
        # pipeline.parse_query_params. If that pipeline step ever moves later
        # in the pipeline stack, we'd need to validate this value because it
        # would be an injection point for attacker data.
        auth_entry = request.session.get(pipeline.AUTH_ENTRY_KEY)
        # Fall back to django settings's SOCIAL_AUTH_LOGIN_ERROR_URL.
        return '/' + auth_entry if auth_entry else super(ExceptionMiddleware, self).get_redirect_uri(request, exception)
