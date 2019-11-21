from importlib import import_module

from django.http import Http404
from django.shortcuts import get_object_or_404

from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from .models import Partner

PARTNERS_VIEW_FRMT = 'openedx.features.partners.{slug}.views'


def dashboard(request, slug):
    partner = get_object_or_404(Partner, slug=slug)
    try:
        views = import_module(PARTNERS_VIEW_FRMT.format(slug=partner.slug))
        return views.dashboard(request, partner.slug)
    except ImportError:
        raise Http404('Your partner is not properly registered')


@require_http_methods(["POST"])
@sensitive_post_parameters('password')
def register_user(request, slug):
    """
    This is general registering view, for users of all partners
    :param request: The Django request.
    :param slug: partner slug
    :return: JsonResponse object with success/error message
    """
    partner = get_object_or_404(Partner, slug=slug)

    try:
        views = import_module(PARTNERS_VIEW_FRMT.format(slug=partner.slug))
        return views.Give2AsiaRegistrationView.as_view()(request, partner=partner)
    except ImportError:
        raise Http404('Your partner is not properly registered')


@require_http_methods(["POST"])
@sensitive_post_parameters('password')
def login_user(request, slug):
    """
    This is general login view, for users of all partners
    :param request: The Django request.
    :param slug: partner slug
    :return: JsonResponse object with success/error message
    """
    partner = get_object_or_404(Partner, slug=slug)

    try:
        views = import_module(PARTNERS_VIEW_FRMT.format(slug=partner.slug))
        return views.LoginSessionViewG2A.as_view()(request, partner=partner)
    except ImportError:
        raise Http404('Your partner is not properly registered')

