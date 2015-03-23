""" Commerce views. """
import logging

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_406_NOT_ACCEPTABLE, HTTP_202_ACCEPTED, HTTP_409_CONFLICT
from rest_framework.views import APIView

from commerce.api import EcommerceAPI
from commerce.constants import OrderStatus, Messages
from commerce.exceptions import ApiError, InvalidConfigurationError
from commerce.http import DetailResponse, InternalRequestErrorResponse
from course_modes.models import CourseMode
from courseware import courses
from enrollment.api import add_enrollment
from student.models import CourseEnrollment
from util.authentication import SessionAuthenticationAllowInactiveUser


log = logging.getLogger(__name__)


class OrdersView(APIView):
    """ Creates an order with a course seat and enrolls users. """

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
        Attempt to create the order and enroll the user.
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
            order_number, order_status, _body = api.create_order(user, honor_mode.sku)
            if order_status == OrderStatus.COMPLETE:
                msg = Messages.ORDER_COMPLETED.format(order_number=order_number)
                log.debug(msg)
                return DetailResponse(msg)
            else:
                # TODO Before this functionality is fully rolled-out, this branch should be updated to NOT enroll the
                # user. Enrollments must be initiated by the E-Commerce API only.
                self._enroll(course_key, user)
                msg = u'Order %(order_number)s was received with %(status)s status. Expected %(complete_status)s. ' \
                      u'User %(username)s was enrolled in %(course_id)s by LMS.'
                msg_kwargs = {
                    'order_number': order_number,
                    'status': order_status,
                    'complete_status': OrderStatus.COMPLETE,
                    'username': user.username,
                    'course_id': course_id,
                }
                log.error(msg, msg_kwargs)

                msg = Messages.ORDER_INCOMPLETE_ENROLLED.format(order_number=order_number)
                return DetailResponse(msg, status=HTTP_202_ACCEPTED)
        except ApiError as err:
            # The API will handle logging of the error.
            return InternalRequestErrorResponse(err.message)
