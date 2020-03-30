"""
Index view for the support app.
"""


from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from edxmako.shortcuts import render_to_response
from support.decorators import require_support_permission

SUPPORT_INDEX_URLS = [
    {
        "url": reverse_lazy("support:certificates"),
        "name": _("Certificates"),
        "description": _("View and regenerate certificates."),
    },

    # DEPRECATION WARNING: We can remove this end-point
    # once shoppingcart has been replaced by the E-Commerce service.
    {
        "url": reverse_lazy("support:refund"),
        "name": _("Manual Refund"),
        "description": _("Track refunds issued directly through CyberSource."),
    },
    {
        "url": reverse_lazy("support:enrollment"),
        "name": _("Enrollment"),
        "description": _("View and update learner enrollments."),
    },
    {
        "url": reverse_lazy("support:manage_user"),
        "name": _("Manage User"),
        "description": _("Disable User Account"),
    },
    {
        "url": reverse_lazy("support:course_entitlement"),
        "name": _("Entitlements"),
        "description": _("View, create, and reissue learner entitlements"),
    },
    {
        "url": reverse_lazy("support:feature_based_enrollments"),
        "name": _("Feature Based Enrollments"),
        "description": _("View feature based enrollment settings"),
    },
    {
        "url": reverse_lazy("support:link_program_enrollments"),
        "name": _("Link Program Enrollments"),
        "description": _("Link LMS users to program enrollments"),
    },
    {
        "url": reverse_lazy("support:program_enrollments_inspector"),
        "name": _("Program Enrollments Inspector Tool"),
        "description": _("Find information related to a learner's program enrollments"),
    },
]


@require_support_permission
def index(request):  # pylint: disable=unused-argument
    """Render the support index view. """
    context = {
        "urls": SUPPORT_INDEX_URLS
    }
    return render_to_response("support/index.html", context)
