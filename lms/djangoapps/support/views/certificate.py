"""
Certificate tool in the student support app.
"""
from django.views.generic import View
from django.utils.decorators import method_decorator

from edxmako.shortcuts import render_to_response
from support.decorators import require_support_permission
import urllib


class CertificatesSupportView(View):
    """
    View for viewing and regenerating certificates for users.

    This is used by the support team to re-issue certificates
    to users if something went wrong during the initial certificate generation,
    such as:

    * The user's name was spelled incorrectly.
    * The user later earned a higher grade and wants it on his/her certificate and dashboard.
    * The user accidentally received an honor code certificate because his/her
        verification expired before certs were generated.

    Most of the heavy lifting is performed client-side through API
    calls directly to the certificates app.

    """

    @method_decorator(require_support_permission)
    def get(self, request):
        """Render the certificates support view. """
        context = {
            "user_filter": urllib.unquote(urllib.quote_plus(request.GET.get("user", ""))),
            "course_filter": request.GET.get("course_id", "")
        }
        return render_to_response("support/certificates.html", context)
