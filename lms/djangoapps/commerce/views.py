""" Commerce views. """
import logging

from django.conf import settings
from django.views.decorators.cache import cache_page
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_406_NOT_ACCEPTABLE, HTTP_409_CONFLICT
from rest_framework.views import APIView

from commerce.api import EcommerceAPI
from commerce.constants import Messages
from commerce.exceptions import ApiError, InvalidConfigurationError, InvalidResponseError
from commerce.http import DetailResponse, InternalRequestErrorResponse
from course_modes.models import CourseMode
from courseware import courses
from edxmako.shortcuts import render_to_response
from enrollment.api import add_enrollment
from microsite_configuration import microsite
from openedx.core.lib.api.authentication import SessionAuthenticationAllowInactiveUser
from student.models import CourseEnrollment
from util.json_request import JsonResponse


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

        # Setup the API and report any errors if settings are not valid.
        try:
            api = EcommerceAPI()
        except InvalidConfigurationError:
            self._enroll(course_key, user)
            msg = Messages.NO_ECOM_API.format(username=user.username, course_id=unicode(course_key))
            log.debug(msg)
            return DetailResponse(msg)

        # Make the API call
        try:
            response_data = api.create_basket(
                user,
                honor_mode.sku,
                payment_processor="cybersource",
            )
            payment_data = response_data["payment_data"]
            if payment_data is not None:
                # it is time to start the payment flow.
                # NOTE this branch does not appear to be used at the moment.
                return JsonResponse(payment_data)
            elif response_data['order']:
                # the order was completed immediately because there was no charge.
                msg = Messages.ORDER_COMPLETED.format(order_number=response_data['order']['number'])
                log.debug(msg)
                return DetailResponse(msg)
            else:
                # Enroll in the honor mode directly as a failsafe.
                # This MUST be removed when this code handles paid modes.
                self._enroll(course_key, user)
                msg = u'Unexpected response from basket endpoint.'
                log.error(
                    msg + u' Could not enroll user %(username)s in course %(course_id)s.',
                    {'username': user.id, 'course_id': course_id},
                )
                raise InvalidResponseError(msg)
        except ApiError as err:
            # The API will handle logging of the error.
            return InternalRequestErrorResponse(err.message)


@cache_page(1800)
def checkout_cancel(_request):
    """ Checkout/payment cancellation view. """
    context = {'payment_support_email': microsite.get_value('payment_support_email', settings.PAYMENT_SUPPORT_EMAIL)}
    return render_to_response("commerce/checkout_cancel.html", context)
