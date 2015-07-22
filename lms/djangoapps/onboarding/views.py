"""HTTP endpoints for the Teams API."""

from django.shortcuts import render_to_response
from django.http import Http404
from django.conf import settings
from django.views.generic.base import View


class HomePageView(View):
    """
    View methods related to the home page.
    """

    def get(self, request):
        """
        Renders the home page.
        """
        context = {}
        return render_to_response("onboarding/index.html", context)
