"""Middleware classes for third_party_auth."""

from social.apps.django_app.middleware import SocialAuthExceptionMiddleware

from . import pipeline


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


class PipelineQuarantineMiddleware(object):
    """
    Middleware flushes the session if a user agent with a quarantined session
    attempts to leave the quarantined set of views.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):  # pylint: disable=unused-argument
        """
        Check the session to see if we've quarantined the user to a particular
        step of the authentication pipeline; if so, look up which modules the
        user is allowed to browse to without breaking the pipeline. If the view
        that's been requested is outside those modules, then flush the session.

        In general, this middleware should be used in cases where allowing the
        user to exit the running pipeline would be undesirable, and where it'd
        be better to flush the session state rather than allow it. Pipeline
        quarantining is utilized by the Enterprise application to enforce
        collection of user consent for sharing data with a linked third-party
        authentication provider.
        """
        running_pipeline = request.session.get('partial_pipeline')

        if not running_pipeline:
            return

        view_module = view_func.__module__
        quarantined_modules = request.session.get('third_party_auth_quarantined_modules', None)
        if quarantined_modules is not None and not any(view_module.startswith(mod) for mod in quarantined_modules):
            request.session.flush()
