""" Commerce views. """
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt

from commerce.models import CommerceConfiguration
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from openedx.core.djangoapps.theming.helpers import is_request_in_themed_site
from shoppingcart.processors.CyberSource2 import is_user_payment_error
from openedx.core.djangoapps.edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from opaque_keys.edx.locator import CourseLocator
from student.models import CourseEnrollment
from util.json_request import JsonResponse
from django.views.decorators.http import require_http_methods
from course_modes.models import CourseMode
from django.http import HttpResponseBadRequest

log = logging.getLogger(__name__)


@csrf_exempt
def checkout_cancel(_request):
    """ Checkout/payment cancellation view. """
    context = {
        'payment_support_email': configuration_helpers.get_value(
            'payment_support_email', settings.PAYMENT_SUPPORT_EMAIL,
        )
    }
    return render_to_response("commerce/checkout_cancel.html", context)


@csrf_exempt
def checkout_error(_request):
    """ Checkout/payment error view. """
    context = {
        'payment_support_email': configuration_helpers.get_value(
            'payment_support_email', settings.PAYMENT_SUPPORT_EMAIL,
        )
    }
    return render_to_response("commerce/checkout_error.html", context)


@csrf_exempt
@login_required
def checkout_receipt(request):
    """ Receipt view. """

    page_title = _('Receipt')
    is_payment_complete = True
    payment_support_email = configuration_helpers.get_value('payment_support_email', settings.PAYMENT_SUPPORT_EMAIL)
    payment_support_link = '<a href=\"mailto:{email}\">{email}</a>'.format(email=payment_support_email)

    is_cybersource = all(k in request.POST for k in ('signed_field_names', 'decision', 'reason_code'))
    if is_cybersource and request.POST['decision'] != 'ACCEPT':
        # Cybersource may redirect users to this view if it couldn't recover
        # from an error while capturing payment info.
        is_payment_complete = False
        page_title = _('Payment Failed')
        reason_code = request.POST['reason_code']
        # if the problem was with the info submitted by the user, we present more detailed messages.
        if is_user_payment_error(reason_code):
            error_summary = _("There was a problem with this transaction. You have not been charged.")
            error_text = _(
                "Make sure your information is correct, or try again with a different card or another form of payment."
            )
        else:
            error_summary = _("A system error occurred while processing your payment. You have not been charged.")
            error_text = _("Please wait a few minutes and then try again.")
        for_help_text = _("For help, contact {payment_support_link}.").format(payment_support_link=payment_support_link)
    else:
        # if anything goes wrong rendering the receipt, it indicates a problem fetching order data.
        error_summary = _("An error occurred while creating your receipt.")
        error_text = None  # nothing particularly helpful to say if this happens.
        for_help_text = _(
            "If your course does not appear on your dashboard, contact {payment_support_link}."
        ).format(payment_support_link=payment_support_link)

    commerce_configuration = CommerceConfiguration.current()
    # user order cache should be cleared when a new order is placed
    # so user can see new order in their order history.
    if is_payment_complete and commerce_configuration.enabled and commerce_configuration.is_cache_enabled:
        cache_key = commerce_configuration.CACHE_KEY + '.' + str(request.user.id)
        cache.delete(cache_key)

    context = {
        'page_title': page_title,
        'is_payment_complete': is_payment_complete,
        'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
        'verified': SoftwareSecurePhotoVerification.verification_valid_or_pending(request.user).exists(),
        'error_summary': error_summary,
        'error_text': error_text,
        'for_help_text': for_help_text,
        'payment_support_email': payment_support_email,
        'username': request.user.username,
        'nav_hidden': True,
        'is_request_in_themed_site': is_request_in_themed_site()
    }
    return render_to_response('commerce/checkout_receipt.html', context)


@require_http_methods(["GET"])
@login_required
def user_verification_status(request):
    """
    Check for user verification status.
    :return 'True' if the user enrollment for the course belongs to verified modes e.g. Verified, Professional.
    """
    course_id = request.GET.get('course_id', None)

    if course_id is None:
        return HttpResponseBadRequest()

    course_key = CourseLocator.from_string(course_id)
    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(request.user, course_key)
    is_verification_required = enrollment_mode in CourseMode.VERIFIED_MODES

    return JsonResponse({'is_verification_required': is_verification_required})
