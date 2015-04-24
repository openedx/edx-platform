""" Commerce views. """
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
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
from course_modes.models import CourseMode
from courseware import courses
from edxmako.shortcuts import render_to_response
from enrollment.api import add_enrollment
from microsite_configuration import microsite
from student.models import CourseEnrollment
from openedx.core.lib.api.authentication import SessionAuthenticationAllowInactiveUser
from util.json_request import JsonResponse
from verify_student.models import SoftwareSecurePhotoVerification


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
                'payment_processor_name': 'cybersource'
            })

            payment_data = response_data["payment_data"]
            if payment_data:
                # Pass data to the client to begin the payment flow.
                return JsonResponse(payment_data)
            elif response_data['order']:
                # The order was completed immediately because there isno charge.
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


@cache_page(1800)
def checkout_cancel(_request):
    """ Checkout/payment cancellation view. """
    context = {'payment_support_email': microsite.get_value('payment_support_email', settings.PAYMENT_SUPPORT_EMAIL)}
    return render_to_response("commerce/checkout_cancel.html", context)


@csrf_exempt
@login_required
def checkout_receipt(request):
    """ Receipt view. """
    context = {
        'platform_name': microsite.get_value('platform_name', settings.PLATFORM_NAME),
        'verified': SoftwareSecurePhotoVerification.verification_valid_or_pending(request.user).exists()
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
