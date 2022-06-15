import logging
import beeline

from django.shortcuts import redirect, reverse
from django.utils.deprecation import MiddlewareMixin
from django.urls import NoReverseMatch

from tiers.helpers import is_equal_or_sub_url, is_white_listed_url
from tiers.app_settings import settings

from .helpers import get_tier_info


log = logging.getLogger(__name__)


class TahoeTierMiddleware(MiddlewareMixin):
    """
    Django Tiers middleware.

    This is a copy/pasta from `django-tiers` to prepare for AMC shut down.

    # TODO: Clean up AMC-specific legacy.
    """
    @beeline.traced(name="TiersMiddleware.process_request")
    def process_request(self, request):
        """
        Fetch organization from session and deny access to the system if the tier
        is expired
        """
        # If we're already on the url where we have to be, do nothing
        expired_redirect_url = settings.expired_redirect_url()
        if expired_redirect_url and is_equal_or_sub_url(request_url=request.path, checked_url=expired_redirect_url):
            beeline.add_context_field("tiers.no_action_required", True)
            return

        # try/catch needed because the URLs don't necessarily exist both in LMS and CMS
        try:
            # If we're trying to log out or release a hijacked user, don't redirect to expired page
            if request.path == reverse("release_hijack") or request.path == reverse("account_logout"):
                return
        except NoReverseMatch:
            pass

        # If the user has superuser privileges don't do anything
        if request.user.is_authenticated and request.user.is_superuser:
            return

        tier_info = get_tier_info(request)

        if not tier_info:
            # Yes, errors in fetching the TierInfo are ignored completely, this is mostly to avoid having LMS go down
            # if AMC database is down.
            beeline.add_context_field("tiers.no_tier_info", True)
            return

        # Only display expiration warning for Trial tiers for now
        request.session['DISPLAY_EXPIRATION_WARNING'] = tier_info.should_show_expiration_warning()
        request.session['TIER_EXPIRES_IN'] = tier_info.time_til_expiration()
        beeline.add_context_field("tiers.tier_expires_in", request.session['TIER_EXPIRES_IN'])
        # TODO: I'm not sure if we have to refresh the session info at this point somehow.
        request.session['TIER_EXPIRED'] = tier_info.has_subscription_ended()
        beeline.add_context_field("tiers.tier_expired", request.session['TIER_EXPIRED'])
        # TODO: We should use request.TIER_NAME instead of meddling the session, but being consistent for now
        request.session['TIER_NAME'] = tier_info.tier
        beeline.add_context_field("tiers.tier_name", tier_info.tier)

        # TODO: I'm not sure if we have to refresh the session info at this point somehow.
        if tier_info.has_subscription_ended():
            if expired_redirect_url and not is_white_listed_url(request.path):
                return redirect(expired_redirect_url)
