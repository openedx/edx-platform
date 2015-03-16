""" Commerce views. """
import json
import logging
from simplejson import JSONDecodeError

from django.conf import settings
import jwt
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_406_NOT_ACCEPTABLE, HTTP_202_ACCEPTED, HTTP_200_OK
from rest_framework.views import APIView

from commerce.constants import OrderStatus, Messages
from commerce.http import DetailResponse, ApiErrorResponse
from course_modes.models import CourseMode
from courseware import courses
from enrollment.api import add_enrollment
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

    def _get_jwt(self, user, ecommerce_api_signing_key):
        """
        Returns a JWT object with the specified user's info.

        """
        data = {
            'username': user.username,
            'email': user.email
        }
        return jwt.encode(data, ecommerce_api_signing_key)

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

        # Ensure that the E-Commerce API is setup properly
        ecommerce_api_url = getattr(settings, 'ECOMMERCE_API_URL', None)
        ecommerce_api_signing_key = getattr(settings, 'ECOMMERCE_API_SIGNING_KEY', None)

        if not (ecommerce_api_url and ecommerce_api_signing_key):
            self._enroll(course_key, user)
            msg = Messages.NO_ECOM_API.format(username=user.username, course_id=unicode(course_key))
            log.debug(msg)
            return DetailResponse(msg)

        # Default to honor mode. In the future we may expand this view to support additional modes.
        mode = CourseMode.DEFAULT_MODE_SLUG
        course_modes = CourseMode.objects.filter(course_id=course_key, mode_slug=mode, sku__isnull=False)

        # If there are no course modes with SKUs, enroll the user without contacting the external API.
        if not course_modes.exists():
            msg = Messages.NO_SKU_ENROLLED.format(enrollment_mode=mode, course_id=unicode(course_key),
                                                  username=user.username)
            log.debug(msg)
            self._enroll(course_key, user)
            return DetailResponse(msg)

        # Contact external API
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'JWT {}'.format(self._get_jwt(user, ecommerce_api_signing_key))
        }

        url = '{}/orders/'.format(ecommerce_api_url.strip('/'))

        try:
            timeout = getattr(settings, 'ECOMMERCE_API_TIMEOUT', 5)
            response = requests.post(url, data=json.dumps({'sku': course_modes[0].sku}), headers=headers,
                                     timeout=timeout)
        except Exception as ex:  # pylint: disable=broad-except
            log.exception('Call to E-Commerce API failed: %s.', ex.message)
            return ApiErrorResponse()

        status_code = response.status_code

        try:
            data = response.json()
        except JSONDecodeError:
            log.error('E-Commerce API response is not valid JSON.')
            return ApiErrorResponse()

        if status_code == HTTP_200_OK:
            order_number = data.get('number')
            order_status = data.get('status')
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
                    'course_id': unicode(course_key),
                }
                log.error(msg, msg_kwargs)

                msg = Messages.ORDER_INCOMPLETE_ENROLLED.format(order_number=order_number)
                return DetailResponse(msg, status=HTTP_202_ACCEPTED)
        else:
            msg = u'Response from E-Commerce API was invalid: (%(status)d) - %(msg)s'
            msg_kwargs = {
                'status': status_code,
                'msg': data.get('user_message'),
            }
            log.error(msg, msg_kwargs)

            return ApiErrorResponse()
