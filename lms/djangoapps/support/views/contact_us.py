"""
Signle support contact view
"""
from django.views.generic import View

from edxmako.shortcuts import render_to_response


#TODO https://openedx.atlassian.net/browse/LEARNER-2296
class ContactUsView(View):
    """
    View for viewing and submitting contact us form.
    """

    def get(self, request):
        return render_to_response("support/contact_us.html")
