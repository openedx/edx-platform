"""
Studio views for the tiers app.
"""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from tahoe_sites.api import get_organization_for_user


class SiteUnavailableRedirectView(TemplateView):
    """
    Studio Site Unavailable view.

    This works in the Studio and shows a message.
    """
    template_name = 'site-unavailable.html'

    def get_context_data(self, **kwargs):
        context = super(SiteUnavailableRedirectView, self).get_context_data(**kwargs)
        context['organization'] = get_organization_for_user(self.request.user)
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super(SiteUnavailableRedirectView, self).get(request, *args, **kwargs)
