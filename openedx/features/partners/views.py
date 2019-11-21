from importlib import import_module

from django.http import Http404
from django.shortcuts import get_object_or_404

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from rest_framework import status

from student.views import password_change_request_handler

from .forms import PartnerResetPasswordForm
from .models import Partner

PARTNERS_VIEW_FRMT = 'openedx.features.partners.{slug}.views'


def dashboard(request, slug):
    partner = get_object_or_404(Partner, slug=slug)
    try:
        views = import_module(PARTNERS_VIEW_FRMT.format(slug=partner.slug))
        return views.dashboard(request, partner.slug)
    except ImportError:
        raise Http404('Your partner is not properly registered')


@csrf_exempt
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


@csrf_exempt
@require_http_methods(['POST'])
def reset_password_view(request):
    """
    This is the basic password reset view, as per the requirements
    of organization password reset flow. Have to send 404 if user does
    not exist
    :param request: The HttpRequest request object.
    :return: HTTPResponse/JSONResponse object with success/error status code
    """
    email = request.POST.get('email')
    reset_password_form = PartnerResetPasswordForm(data={'email': email})
    if reset_password_form.is_valid():
            response = password_change_request_handler(request)
            if response.status_code == status.HTTP_403_FORBIDDEN:
                return JsonResponse({"Error": {"email": [response.content]}}, status=status.HTTP_403_FORBIDDEN)
            else:
                return response
    else:
        return JsonResponse({"Error": dict(reset_password_form.errors.items())}, status=status.HTTP_404_NOT_FOUND)
