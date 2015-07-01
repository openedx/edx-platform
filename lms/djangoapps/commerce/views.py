""" Commerce views. """
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from ecommerce_api_client import exceptions
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_406_NOT_ACCEPTABLE, HTTP_409_CONFLICT
from rest_framework.views import APIView

from commerce import ecommerce_api_client
from commerce.constants import Messages
from commerce.exceptions import InvalidResponseError
from commerce.http import DetailResponse, InternalRequestErrorResponse
from commerce.utils import audit_log
from course_modes.models import CourseMode
from courseware import courses
from edxmako.shortcuts import render_to_response
from enrollment.api import add_enrollment
from embargo import api as embargo_api
from microsite_configuration import microsite
from student.models import CourseEnrollment
from openedx.core.lib.api.authentication import SessionAuthenticationAllowInactiveUser
from util.json_request import JsonResponse
from verify_student.models import SoftwareSecurePhotoVerification
from shoppingcart.processors.CyberSource2 import is_user_payment_error
from django.utils.translation import ugettext as _


log = logging.getLogger(__name__)


class BasketsView(APIView):
    """ Creates a basket with a course seat and enrolls users. """

    # LMS utilizes User.user_is_active to indicate email verification, not whether an account is active. Sigh!
    authentication_classes = (SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    def _is_data_valid(self, request):
        """
        Validates the data posted to the view.

        Arguments
            request -- HTTP request

        Returns
            Tuple (data_is_valid, course_key, error_msg)
        """
        course_id = request.DATA.get('course_id')

        if not course_id:
            return False, None, u'Field course_id is missing.'

        try:
            course_key = CourseKey.from_string(course_id)
            courses.get_course(course_key)
        except (InvalidKeyError, ValueError)as ex:
            log.exception(u'Unable to locate course matching %s.', course_id)
            return False, None, ex.message

        return True, course_key, None

    def _enroll(self, course_key, user):
        """ Enroll the user in the course. """
        add_enrollment(user.username, unicode(course_key))

    def post(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Attempt to create the basket and enroll the user.
        """
        user = request.user
        valid, course_key, error = self._is_data_valid(request)
        if not valid:
            return DetailResponse(error, status=HTTP_406_NOT_ACCEPTABLE)

        embargo_response = embargo_api.get_embargo_response(request, course_key, user)

        if embargo_response:
            return embargo_response

        # Don't do anything if an enrollment already exists
        course_id = unicode(course_key)
        enrollment = CourseEnrollment.get_enrollment(user, course_key)
        if enrollment and enrollment.is_active:
            msg = Messages.ENROLLMENT_EXISTS.format(course_id=course_id, username=user.username)
            return DetailResponse(msg, status=HTTP_409_CONFLICT)

        # If there is no honor course mode, this most likely a Prof-Ed course. Return an error so that the JS
        # redirects to track selection.
        honor_mode = CourseMode.mode_for_course(course_key, CourseMode.HONOR)

        if not honor_mode:
            msg = Messages.NO_HONOR_MODE.format(course_id=course_id)
            return DetailResponse(msg, status=HTTP_406_NOT_ACCEPTABLE)
        elif not honor_mode.sku:
            # If there are no course modes with SKUs, enroll the user without contacting the external API.
            msg = Messages.NO_SKU_ENROLLED.format(enrollment_mode=CourseMode.HONOR, course_id=course_id,
                                                  username=user.username)
            log.debug(msg)
            self._enroll(course_key, user)
            return DetailResponse(msg)

        # Setup the API

        try:
            api = ecommerce_api_client(user)
        except ValueError:
            self._enroll(course_key, user)
            msg = Messages.NO_ECOM_API.format(username=user.username, course_id=unicode(course_key))
            log.debug(msg)
            return DetailResponse(msg)

        # Make the API call
        try:
            response_data = api.baskets.post({
                'products': [{'sku': honor_mode.sku}],
                'checkout': True,
            })

            payment_data = response_data["payment_data"]
            if payment_data:
                # Pass data to the client to begin the payment flow.
                return JsonResponse(payment_data)
            elif response_data['order']:
                # The order was completed immediately because there is no charge.
                msg = Messages.ORDER_COMPLETED.format(order_number=response_data['order']['number'])
                log.debug(msg)
                return DetailResponse(msg)
            else:
                msg = u'Unexpected response from basket endpoint.'
                log.error(
                    msg + u' Could not enroll user %(username)s in course %(course_id)s.',
                    {'username': user.id, 'course_id': course_id},
                )
                raise InvalidResponseError(msg)
        except (exceptions.SlumberBaseException, exceptions.Timeout) as ex:
            log.exception(ex.message)
            return InternalRequestErrorResponse(ex.message)
        finally:
            audit_log(
                'checkout_requested',
                course_id=course_id,
                mode=honor_mode.slug,
                processor_name=None,
                user_id=user.id
            )


@csrf_exempt
def checkout_cancel(_request):
    """ Checkout/payment cancellation view. """
    context = {'payment_support_email': microsite.get_value('payment_support_email', settings.PAYMENT_SUPPORT_EMAIL)}
    return render_to_response("commerce/checkout_cancel.html", context)


@csrf_exempt
@login_required
def checkout_receipt(request):
    """ Receipt view. """

    page_title = _('Receipt')
    is_payment_complete = True
    payment_support_email = microsite.get_value('payment_support_email', settings.PAYMENT_SUPPORT_EMAIL)
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

    context = {
        'page_title': page_title,
        'is_payment_complete': is_payment_complete,
        'platform_name': microsite.get_value('platform_name', settings.PLATFORM_NAME),
        'verified': SoftwareSecurePhotoVerification.verification_valid_or_pending(request.user).exists(),
        'error_summary': error_summary,
        'error_text': error_text,
        'for_help_text': for_help_text,
        'payment_support_email': payment_support_email,
    }
    return render_to_response('commerce/checkout_receipt.html', context)


class BasketOrderView(APIView):
    """ Retrieve the order associated with a basket. """

    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *_args, **kwargs):
        """ HTTP handler. """
        try:
            order = ecommerce_api_client(request.user).baskets(kwargs['basket_id']).order.get()
            return JsonResponse(order)
        except exceptions.HttpNotFoundError:
            return JsonResponse(status=404)
