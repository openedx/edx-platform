""" API v0 views. """
import logging

from edx_rest_api_client import exceptions
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_406_NOT_ACCEPTABLE, HTTP_409_CONFLICT
from rest_framework.views import APIView

from commerce.constants import Messages
from commerce.exceptions import InvalidResponseError
from commerce.http import DetailResponse, InternalRequestErrorResponse
from commerce.utils import audit_log
from course_modes.models import CourseMode
from courseware import courses
from embargo import api as embargo_api
from enrollment.api import add_enrollment
from enrollment.views import EnrollmentCrossDomainSessionAuth
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from openedx.core.djangoapps.user_api.preferences.api import update_email_opt_in
from openedx.core.lib.api.authentication import OAuth2AuthenticationAllowInactiveUser
from student.models import CourseEnrollment
from util.json_request import JsonResponse


log = logging.getLogger(__name__)


class BasketsView(APIView):
    """ Creates a basket with a course seat and enrolls users. """

    # LMS utilizes User.user_is_active to indicate email verification, not whether an account is active. Sigh!
    authentication_classes = (EnrollmentCrossDomainSessionAuth, OAuth2AuthenticationAllowInactiveUser)
    permission_classes = (IsAuthenticated,)

    def _is_data_valid(self, request):
        """
        Validates the data posted to the view.

        Arguments
            request -- HTTP request

        Returns
            Tuple (data_is_valid, course_key, error_msg)
        """
        course_id = request.data.get('course_id')

        if not course_id:
            return False, None, u'Field course_id is missing.'

        try:
            course_key = CourseKey.from_string(course_id)
            courses.get_course(course_key)
        except (InvalidKeyError, ValueError)as ex:
            log.exception(u'Unable to locate course matching %s.', course_id)
            return False, None, ex.message

        return True, course_key, None

    def _enroll(self, course_key, user, mode=CourseMode.DEFAULT_MODE_SLUG):
        """ Enroll the user in the course. """
        add_enrollment(user.username, unicode(course_key), mode)

    def _handle_marketing_opt_in(self, request, course_key, user):
        """
        Handle the marketing email opt-in flag, if it was set.

        Errors here aren't expected, but should not break the outer enrollment transaction.
        """
        email_opt_in = request.data.get('email_opt_in', None)
        if email_opt_in is not None:
            try:
                update_email_opt_in(user, course_key.org, email_opt_in)
            except Exception:  # pylint: disable=broad-except
                # log the error, return silently
                log.exception(
                    'Failed to handle marketing opt-in flag: user="%s", course="%s"', user.username, course_key
                )

    def post(self, request, *args, **kwargs):
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

        # Check to see if enrollment for this course is closed.
        course = courses.get_course(course_key)
        if CourseEnrollment.is_enrollment_closed(user, course):
            msg = Messages.ENROLLMENT_CLOSED.format(course_id=course_id)
            log.info(u'Unable to enroll user %s in closed course %s.', user.id, course_id)
            return DetailResponse(msg, status=HTTP_406_NOT_ACCEPTABLE)

        # If there is no audit or honor course mode, this most likely
        # a Prof-Ed course. Return an error so that the JS redirects
        # to track selection.
        honor_mode = CourseMode.mode_for_course(course_key, CourseMode.HONOR)
        audit_mode = CourseMode.mode_for_course(course_key, CourseMode.AUDIT)

        # Accept either honor or audit as an enrollment mode to
        # maintain backwards compatibility with existing courses
        default_enrollment_mode = audit_mode or honor_mode

        if not default_enrollment_mode:
            msg = Messages.NO_DEFAULT_ENROLLMENT_MODE.format(course_id=course_id)
            return DetailResponse(msg, status=HTTP_406_NOT_ACCEPTABLE)
        elif default_enrollment_mode and not default_enrollment_mode.sku:
            # If there are no course modes with SKUs, enroll the user without contacting the external API.
            msg = Messages.NO_SKU_ENROLLED.format(
                enrollment_mode=default_enrollment_mode.slug,
                course_id=course_id,
                username=user.username
            )
            log.info(msg)
            self._enroll(course_key, user, default_enrollment_mode.slug)
            self._handle_marketing_opt_in(request, course_key, user)
            return DetailResponse(msg)

        # Setup the API

        try:
            api = ecommerce_api_client(user)
        except ValueError:
            self._enroll(course_key, user)
            msg = Messages.NO_ECOM_API.format(username=user.username, course_id=unicode(course_key))
            log.debug(msg)
            return DetailResponse(msg)

        response = None

        # Make the API call
        try:
            response_data = api.baskets.post({
                'products': [{'sku': default_enrollment_mode.sku}],
                'checkout': True,
            })

            payment_data = response_data["payment_data"]
            if payment_data:
                # Pass data to the client to begin the payment flow.
                response = JsonResponse(payment_data)
            elif response_data['order']:
                # The order was completed immediately because there is no charge.
                msg = Messages.ORDER_COMPLETED.format(order_number=response_data['order']['number'])
                log.debug(msg)
                response = DetailResponse(msg)
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
                mode=default_enrollment_mode.slug,
                processor_name=None,
                user_id=user.id
            )

        self._handle_marketing_opt_in(request, course_key, user)
        return response


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
