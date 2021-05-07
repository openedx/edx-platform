"""
All views for webinars app
"""
from django.views.generic.detail import DetailView

from .models import Webinar


class WebinarDetailView(DetailView):
    """
    A view to get description about a specific webinar.
    """

    model = Webinar
    template_name = 'adg/lms/webinar/description_page.html'
