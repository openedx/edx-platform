"""
Views for the tiers app.
"""

from django.views.generic import TemplateView


class SiteUnavailableView(TemplateView):
    """
    LMS Site Unavailable view.

    This works in the LMS and shows a message.
    """
    template_name = 'site-unavailable.html'
