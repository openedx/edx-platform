"""
The Enrollment API Views should be simple, lean HTTP endpoints for API access. This should
consist primarily of authentication, request validation, and serialization.

"""
import logging

from ipware.ip import get_ip
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from opaque_keys import InvalidKeyError
from course_modes.models import CourseMode
from lms.djangoapps.commerce.utils import audit_log
from openedx.core.djangoapps.user_api.preferences.api import update_email_opt_in
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission, ApiKeyHeaderPermissionIsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from opaque_keys.edx.keys import CourseKey
from embargo import api as embargo_api
from cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.core.lib.api.authentication import (
    SessionAuthenticationAllowInactiveUser,
    OAuth2AuthenticationAllowInactiveUser,
)
from util.disable_rate_limit import can_disable_rate_limit
from enrollment import api
from enrollment.errors import (
    CourseNotFoundError, CourseEnrollmentError,
    CourseModeNotFoundError, CourseEnrollmentExistsError
)
from student.models import User

log = logging.getLogger(__name__)


class EnrollmentCrossDomainSessionAuth(SessionAuthenticationAllowInactiveUser, SessionAuthenticationCrossDomainCsrf):
    """Session authentication that allows inactive users and cross-domain requests. """
    pass


class ApiKeyPermissionMixIn(object):
    """
    This mixin is used to provide a convenience function for doing individual permission checks
    for the presence of API keys.
    """
    def has_api_key_permissions(self, request):
        """
        Checks to see if the request was made by a server with an API key.

        Args:
            request (Request): the request being made into the view

        Return:
            True if the request has been made with a valid API key
            False otherwise
        """
        return ApiKeyHeaderPermission().has_permission(request, self)


class EnrollmentUserThrottle(UserRateThrottle, ApiKeyPermissionMixIn):
    """Limit the number of requests users can make to the enrollment API."""
    rate = '40/minute'

    def allow_request(self, request, view):
        return self.has_api_key_permissions(request) or super(EnrollmentUserThrottle, self).allow_request(request, view)


@can_disable_rate_limit
class EnrollmentView(APIView, ApiKeyPermissionMixIn):
    """
        **Use Cases**

            Get the user's enrollment status for a course.

        **Example Requests**:

            GET /api/enrollment/v1/enrollment/{username},{course_id}

        **Response Values**

            * created: The date the user account was created.

            * mode: The enrollment mode of the user in this course.

            * is_active: Whether the enrollment is currently active.

            * course_details: A collection that includes:

                * course_id: The unique identifier for the course.

                * enrollment_start: The date and time that users can begin enrolling in the course.
                  If null, enrollment opens immediately when the course is created.

                * enrollment_end: The date and time after which users cannot enroll for the course.
                  If null, the enrollment period never ends.

                * course_start: The date and time at which the course opens.
                  If null, the course opens immediately when created.

                * course_end: The date and time at which the course closes.  If null, the course never ends.

                * course_modes: An array of data about the enrollment modes supported for the course.
                  Each enrollment mode collection includes:

                    * slug: The short name for the enrollment mode.
                    * name: The full name of the enrollment mode.
                    * min_price: The minimum price for which a user can enroll in this mode.
                    * suggested_prices: A list of suggested prices for this enrollment mode.
                    * currency: The currency of the listed prices.
                    * expiration_datetime: The date and time after which users cannot enroll in the course in this mode.
                    * description: A description of this mode.

                * invite_only: Whether students must be invited to enroll in the course; true or false.

            * user: The ID of the user.
    """

    authentication_classes = OAuth2AuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser
    permission_classes = ApiKeyHeaderPermissionIsAuthenticated,
    throttle_classes = EnrollmentUserThrottle,

    # Since the course about page on the marketing site uses this API to auto-enroll users,
    # we need to support cross-domain CSRF.
    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request, course_id=None, username=None):
        """Create, read, or update enrollment information for a user.

        HTTP Endpoint for all CRUD operations for a user course enrollment. Allows creation, reading, and
        updates of the current enrollment for a particular course.

        Args:
            request (Request): To get current course enrollment information, a GET request will return
                information for the current user and the specified course.
            course_id (str): URI element specifying the course location. Enrollment information will be
                returned, created, or updated for this particular course.
            username (str): The username associated with this enrollment request.

        Return:
            A JSON serialized representation of the course enrollment.

        """
        username = username or request.user.username

        # TODO Implement proper permissions
        if request.user.username != username and not self.has_api_key_permissions(request) \
                and not request.user.is_superuser:
            # Return a 404 instead of a 403 (Unauthorized). If one user is looking up
            # other users, do not let them deduce the existence of an enrollment.
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            return Response(api.get_enrollment(username, course_id))
        except CourseEnrollmentError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"An error occurred while retrieving enrollments for user "
                        u"'{username}' in course '{course_id}'"
                    ).format(username=username, course_id=course_id)
                }
            )


@can_disable_rate_limit
class EnrollmentCourseDetailView(APIView):
    """
        **Use Cases**

            Get enrollment details for a course.

            Response values include the course schedule and enrollment modes supported by the course.
            Use the parameter include_expired=1 to include expired enrollment modes in the response.

            **Note:** Getting enrollment details for a course does not require authentication.

        **Example Requests**:

            GET /api/enrollment/v1/course/{course_id}

            GET /api/v1/enrollment/course/{course_id}?include_expired=1


        **Response Values**

            A collection of course enrollments for the user, or for the newly created enrollment.
            Each course enrollment contains:

                * course_id: The unique identifier of the course.

                * enrollment_start: The date and time that users can begin enrolling in the course.
                  If null, enrollment opens immediately when the course is created.

                * enrollment_end: The date and time after which users cannot enroll for the course.
                  If null, the enrollment period never ends.

                * course_start: The date and time at which the course opens.
                  If null, the course opens immediately when created.

                * course_end: The date and time at which the course closes.  If null, the course never ends.

                * course_modes: An array containing details about the enrollment modes supported for the course.
                  If the request uses the parameter include_expired=1, the array also includes expired enrollment modes.

                  Each enrollment mode collection includes:

                        * slug: The short name for the enrollment mode.
                        * name: The full name of the enrollment mode.
                        * min_price: The minimum price for which a user can enroll in this mode.
                        * suggested_prices: A list of suggested prices for this enrollment mode.
                        * currency: The currency of the listed prices.
                        * expiration_datetime: The date and time after which users cannot enroll in the course
                          in this mode.
                        * description: A description of this mode.

                * invite_only: Whether students must be invited to enroll in the course; true or false.
    """

    authentication_classes = []
    permission_classes = []
    throttle_classes = EnrollmentUserThrottle,

    def get(self, request, course_id=None):
        """Read enrollment information for a particular course.

        HTTP Endpoint for retrieving course level enrollment information.

        Args:
            request (Request): To get current course enrollment information, a GET request will return
                information for the specified course.
            course_id (str): URI element specifying the course location. Enrollment information will be
                returned.

        Return:
            A JSON serialized representation of the course enrollment details.

        """
        try:
            return Response(api.get_course_enrollment_details(course_id, bool(request.GET.get('include_expired', ''))))
        except CourseNotFoundError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"No course found for course ID '{course_id}'"
                    ).format(course_id=course_id)
                }
            )


@can_disable_rate_limit
class EnrollmentListView(APIView, ApiKeyPermissionMixIn):
    """
        **Use Cases**

            1. Get a list of all course enrollments for the currently logged in user.

            2. Enroll the currently logged in user in a course.

               Currently a user can use this command only to enroll the user in "honor" mode.

               If honor mode is not supported for the course, the request fails and returns the available modes.

               A server-to-server call can be used by this command to enroll a user in other modes, such as "verified"
               or "professional". If the mode is not supported for the course, the request will fail and return the
               available modes.

        **Example Requests**:

            GET /api/enrollment/v1/enrollment

            POST /api/enrollment/v1/enrollment{"mode": "honor", "course_details":{"course_id": "edX/DemoX/Demo_Course"}}

        **Post Parameters**

            * user:  The username of the currently logged in user. Optional.
              You cannot use the command to enroll a different user.

            * mode: The Course Mode for the enrollment. Individual users cannot upgrade their enrollment mode from
              'honor'. Only server-to-server requests can enroll with other modes. Optional.

            * is_active: A Boolean indicating whether the enrollment is active. Only server-to-server requests are
              allowed to deactivate an enrollment. Optional.

            * course details: A collection that contains:

                * course_id: The unique identifier for the course.

            * email_opt_in: A Boolean indicating whether the user
              wishes to opt into email from the organization running this course. Optional.

        **Response Values**

            A collection of course enrollments for the user, or for the newly created enrollment.
            Each course enrollment contains:

                * created: The date the user account was created.

                * mode: The enrollment mode of the user in this course.

                * is_active: Whether the enrollment is currently active.

                * course_details: A collection that includes:

                    * course_id:  The unique identifier for the course.

                    * enrollment_start: The date and time that users can begin enrolling in the course.
                      If null, enrollment opens immediately when the course is created.

                    * enrollment_end: The date and time after which users cannot enroll for the course.
                      If null, the enrollment period never ends.

                    * course_start: The date and time at which the course opens.
                      If null, the course opens immediately when created.

                    * course_end: The date and time at which the course closes.  If null, the course never ends.

                    * course_modes: An array of data about the enrollment modes supported for the course.
                      Each enrollment mode collection includes:

                        * slug: The short name for the enrollment mode.
                        * name: The full name of the enrollment mode.
                        * min_price: The minimum price for which a user can enroll in this mode.
                        * suggested_prices: A list of suggested prices for this enrollment mode.
                        * currency: The currency of the listed prices.
                        * expiration_datetime: The date and time after which users cannot enroll in the course
                          in this mode.
                        * description: A description of this mode.


                    * invite_only: Whether students must be invited to enroll in the course; true or false.

                * user: The username of the user.
    """

    authentication_classes = OAuth2AuthenticationAllowInactiveUser, EnrollmentCrossDomainSessionAuth
    permission_classes = ApiKeyHeaderPermissionIsAuthenticated,
    throttle_classes = EnrollmentUserThrottle,

    # Since the course about page on the marketing site
    # uses this API to auto-enroll users, we need to support
    # cross-domain CSRF.
    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request):
        """Gets a list of all course enrollments for the currently logged in user."""
        username = request.GET.get('user', request.user.username)
        if request.user.username != username and not self.has_api_key_permissions(request):
            # Return a 404 instead of a 403 (Unauthorized). If one user is looking up
            # other users, do not let them deduce the existence of an enrollment.
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            return Response(api.get_enrollments(username))
        except CourseEnrollmentError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"An error occurred while retrieving enrollments for user '{username}'"
                    ).format(username=username)
                }
            )

    def post(self, request):
        """Enrolls the currently logged-in user in a course.

        Server-to-server calls may deactivate or modify the mode of existing enrollments. All other requests
        go through `add_enrollment()`, which allows creation of new and reactivation of old enrollments.
        """
        # Get the User, Course ID, and Mode from the request.
        username = request.DATA.get('user', request.user.username)
        course_id = request.DATA.get('course_details', {}).get('course_id')

        if not course_id:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": u"Course ID must be specified to create a new enrollment."}
            )

        try:
            course_id = CourseKey.from_string(course_id)
        except InvalidKeyError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": u"No course '{course_id}' found for enrollment".format(course_id=course_id)
                }
            )

        mode = request.DATA.get('mode', CourseMode.HONOR)

        has_api_key_permissions = self.has_api_key_permissions(request)

        # Check that the user specified is either the same user, or this is a server-to-server request.
        if not username:
            username = request.user.username
        if username != request.user.username and not has_api_key_permissions:
            # Return a 404 instead of a 403 (Unauthorized). If one user is looking up
            # other users, do not let them deduce the existence of an enrollment.
            return Response(status=status.HTTP_404_NOT_FOUND)

        if mode != CourseMode.HONOR and not has_api_key_permissions:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": u"User does not have permission to create enrollment with mode [{mode}].".format(
                        mode=mode
                    )
                }
            )

        try:
            # Lookup the user, instead of using request.user, since request.user may not match the username POSTed.
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            return Response(
                status=status.HTTP_406_NOT_ACCEPTABLE,
                data={
                    'message': u'The user {} does not exist.'.format(username)
                }
            )

        embargo_response = embargo_api.get_embargo_response(request, course_id, user)

        if embargo_response:
            return embargo_response

        try:
            is_active = request.DATA.get('is_active')
            # Check if the requested activation status is None or a Boolean
            if is_active is not None and not isinstance(is_active, bool):
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        'message': (u"'{value}' is an invalid enrollment activation status.").format(value=is_active)
                    }
                )

            enrollment = api.get_enrollment(username, unicode(course_id))
            mode_changed = enrollment and mode is not None and enrollment['mode'] != mode
            active_changed = enrollment and is_active is not None and enrollment['is_active'] != is_active
            if has_api_key_permissions and (mode_changed or active_changed):
                if mode_changed and active_changed and not is_active:
                    # if the requester wanted to deactivate but specified the wrong mode, fail
                    # the request (on the assumption that the requester had outdated information
                    # about the currently active enrollment).
                    msg = u"Enrollment mode mismatch: active mode={}, requested mode={}. Won't deactivate.".format(
                        enrollment["mode"], mode
                    )
                    log.warning(msg)
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": msg})
                response = api.update_enrollment(username, unicode(course_id), mode=mode, is_active=is_active)
            else:
                # Will reactivate inactive enrollments.
                response = api.add_enrollment(username, unicode(course_id), mode=mode, is_active=is_active)

            email_opt_in = request.DATA.get('email_opt_in', None)
            if email_opt_in is not None:
                org = course_id.org
                update_email_opt_in(request.user, org, email_opt_in)

            return Response(response)
        except CourseModeNotFoundError as error:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"The course mode '{mode}' is not available for course '{course_id}'."
                    ).format(mode="honor", course_id=course_id),
                    "course_details": error.data
                })
        except CourseNotFoundError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": u"No course '{course_id}' found for enrollment".format(course_id=course_id)
                }
            )
        except CourseEnrollmentExistsError as error:
            return Response(data=error.enrollment)
        except CourseEnrollmentError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"An error occurred while creating the new course enrollment for user "
                        u"'{username}' in course '{course_id}'"
                    ).format(username=username, course_id=course_id)
                }
            )
        finally:
            # Assumes that the ecommerce service uses an API key to authenticate.
            if has_api_key_permissions:
                current_enrollment = api.get_enrollment(username, unicode(course_id))
                audit_log(
                    'enrollment_change_requested',
                    course_id=unicode(course_id),
                    requested_mode=mode,
                    actual_mode=current_enrollment['mode'] if current_enrollment else None,
                    requested_activation=is_active,
                    actual_activation=current_enrollment['is_active'] if current_enrollment else None,
                    user_id=user.id
                )
