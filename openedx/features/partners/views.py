from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from g2a.views import g2a_dashboard
from .g2a.views import Give2AsiaRegistrationView
from .models import Partner


def dashboard(request, slug):
    partner = get_object_or_404(Partner, slug=slug)
    # TODO: we need to make it generic for all partners
    if partner.slug == 'give2asia':
        return g2a_dashboard(request)


@require_http_methods(["POST"])
@sensitive_post_parameters('password')
@csrf_exempt
def register_user(request, slug):
    """
    This is general registering view, for users of all partners
    :param request: The Django request.
    :param slug: partner slug
    :return: JsonResponse object with success/error message
    """
    partner = get_object_or_404(Partner, slug=slug)
    # TODO: we need to make it generic for all partners
    if partner.slug == 'give2asia':
        return Give2AsiaRegistrationView.as_view()(request, partner=partner)
