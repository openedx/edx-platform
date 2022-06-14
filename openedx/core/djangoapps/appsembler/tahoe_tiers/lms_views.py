"""
Views for the tiers app for LMS.

CMS part is in `cms/djangoapps/appsembler_tiers/`.
"""

from django.views.generic import TemplateView


class LMSSiteUnavailableView(TemplateView):
    """
    LMS Site Unavailable view.

    This works in the LMS and shows a message.
    """
    template_name = 'static_templates/site-unavailable.html'
