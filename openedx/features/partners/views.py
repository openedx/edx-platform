from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from rest_framework import status

from student.views import password_change_request_handler

from .forms import PartnerResetPasswordForm
from .helpers import import_module_using_slug, user_has_performance_access
from .models import Partner


def dashboard(request, slug):
    partner = get_object_or_404(Partner, slug=slug)
    views = import_module_using_slug(partner.slug)
    return views.dashboard(request, partner.slug)


def performance_dashboard(request, slug):
    partner = get_object_or_404(Partner, slug=slug)
    if user_has_performance_access(request.user, partner):
        partner_views = import_module_using_slug(partner.slug)
        return partner_views.performance_dashboard(request, partner)
    return HttpResponseForbidden()


@require_http_methods(["POST"])
@sensitive_post_parameters('password')
def register_user(request, slug):
    """
    This is general registering view, for users of all partners
    :param request: The HttpRequest request object.
    :param slug: partner slug
    :return: JsonResponse object with success/error message
    """
    partner = get_object_or_404(Partner, slug=slug)
    views = import_module_using_slug(partner.slug)
    return views.Give2AsiaRegistrationView.as_view()(request, partner=partner)


@require_http_methods(["POST"])
@sensitive_post_parameters('password')
def login_user(request, slug):
    """
    This is general login view, for users of all partners
    :param request: The HttpRequest request object.
    :param slug: partner slug
    :return: JsonResponse object with success/error message
    """
    partner = get_object_or_404(Partner, slug=slug)
    views = import_module_using_slug(partner.slug)
    return views.LoginSessionViewG2A.as_view()(request, partner=partner)


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
        return response
    return JsonResponse({"Error": dict(reset_password_form.errors.items())}, status=status.HTTP_404_NOT_FOUND)
