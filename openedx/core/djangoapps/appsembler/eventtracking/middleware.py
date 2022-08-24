"""
Event-tracking middleware for Tahoe.

Adds additional tracking event context specific to Tahoe.
"""

from eventtracking import tracker

from . import contexts


class TahoeUserEventContextMiddleware:
    """Middleware for adding custom Tahoe user-specific context to tracking events."""

    CONTEXT_NAME = 'tahoe_user_context'

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        context = {}

        # avoid doing additional work if not configured for Site
        # TODO: get SiteConfiguration ... I don't know best way any more!
        # SOMETHING LIKE....
        # if not siteconfig.get_value('TRACKING_EVENTS_ADD_IDP_METADATA', False):
        #     return response

        # Add any IDP Metadata context
        context['tahoe_idp_metadata'] = contexts.user_tahoe_idp_metadata_context(
            request.user.pk
        )

        tracker.get_tracker().enter_context(self.CONTEXT_NAME, context)

        response = self.get_response(request)
        return response
