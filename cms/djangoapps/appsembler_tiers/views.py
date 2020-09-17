"""
Studio views for the tiers app.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import View

from openedx.core.djangoapps.appsembler.sites.utils import (
    get_site_by_organization,
    get_single_user_organization,
)


class SiteUnavailableRedirectView(View):
    """
    Studio view to redirect to the LMS view (above).
    """

    @method_decorator(login_required)
    def get(self, request):
        organization = get_single_user_organization(request.user)
        site = get_site_by_organization(organization)
        return redirect('{protocol}://{domain}{page}'.format(
            protocol='https' if request.is_secure() else 'http',
            domain=site.domain,  # This don't will redirect to the Tahoe domain. Custom domains are not supported yet.
            page=reverse('site_unavailable'),
        ))
