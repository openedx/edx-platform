"""
The Enrollment API Views should be simple, lean HTTP endpoints for API access. This should
consist primarily of authentication, request validation, and serialization.

"""
import logging

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
from student.auth import user_has_role
from student.models import User
from student.roles import CourseStaffRole, GlobalStaff


log = logging.getLogger(__name__)
REQUIRED_ATTRIBUTES = {
    "credit": ["credit:provider_id"],
}


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
        **Use Case**

            Get the user's enrollment status for a course.

        **Example Request**

            GET /api/enrollment/v1/enrollment/{username},{course_id}

        **Response Values**

            If the request for information about the user is successful, an HTTP 200 "OK" response
            is returned.

            The HTTP 200 response has the following values.

            * course_details: A collection that includes the following
              values.

                * course_end: The date and time when the course closes. If
                  null, the course never ends.
                * course_id: The unique identifier for the course.
                * course_modes: An array of data about the enrollment modes
                  supported for the course. If the request uses the parameter
                  include_expired=1, the array also includes expired
                  enrollment modes.

                  Each enrollment mode collection includes the following
                  values.

                        * currency: The currency of the listed prices.
                        * description: A description of this mode.
                        * expiration_datetime: The date and time after which
                          users cannot enroll in the course in this mode.
                        * min_price: The minimum price for which a user can
                          enroll in this mode.
                        * name: The full name of the enrollment mode.
                        * slug: The short name for the enrollment mode.
                        * suggested_prices: A list of suggested prices for
                          this enrollment mode.

                * course_end: The date and time at which the course closes.  If
                  null, the course never ends.
                * course_start: The date and time when the course opens. If
                  null, the course opens immediately when it is created.
                * enrollment_end: The date and time after which users cannot
                  enroll for the course. If null, the enrollment period never
                  ends.
                * enrollment_start: The date and time when users can begin
                  enrolling in the course. If null, enrollment opens
                  immediately when the course is created.
                * invite_only: A value indicating whether students must be
                  invited to enroll in the course. Possible values are true or
                  false.

            * created: The date the user account was created.
            * is_active: Whether the enrollment is currently active.
            * mode: The enrollment mode of the user in this course.
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
        **Use Case**

            Get enrollment details for a course.

            Response values include the course schedule and enrollment modes
            supported by the course. Use the parameter include_expired=1 to
            include expired enrollment modes in the response.

            **Note:** Getting enrollment details for a course does not require
            authentication.

        **Example Requests**

            GET /api/enrollment/v1/course/{course_id}

            GET /api/enrollment/v1/course/{course_id}?include_expired=1

        **Response Values**

            If the request is successful, an HTTP 200 "OK" response is
            returned along with a collection of course enrollments for the
            user or for the newly created enrollment.

            Each course enrollment contains the following values.

                * course_end: The date and time when the course closes. If
                  null, the course never ends.
                * course_id: The unique identifier for the course.
                * course_modes: An array of data about the enrollment modes
                  supported for the course. If the request uses the parameter
                  include_expired=1, the array also includes expired
                  enrollment modes.

                  Each enrollment mode collection includes the following
                  values.

                        * currency: The currency of the listed prices.
                        * description: A description of this mode.
                        * expiration_datetime: The date and time after which
                          users cannot enroll in the course in this mode.
                        * min_price: The minimum price for which a user can
                          enroll in this mode.
                        * name: The full name of the enrollment mode.
                        * slug: The short name for the enrollment mode.
                        * suggested_prices: A list of suggested prices for
                          this enrollment mode.

                * course_start: The date and time when the course opens. If
                  null, the course opens immediately when it is created.
                * enrollment_end: The date and time after which users cannot
                  enroll for the course. If null, the enrollment period never
                  ends.
                * enrollment_start: The date and time when users can begin
                  enrolling in the course. If null, enrollment opens
                  immediately when the course is created.
                * invite_only: A value indicating whether students must be
                  invited to enroll in the course. Possible values are true or
                  false.
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

            * Get a list of all course enrollments for the currently signed in user.

            * Enroll the currently signed in user in a course.

              Currently a user can use this command only to enroll the user in
              honor mode. If honor mode is not supported for the course, the
              request fails and returns the available modes.

              This command can use a server-to-server call to enroll a user in
              other modes, such as "verified", "professional", or "credit". If
              the mode is not supported for the course, the request will fail
              and return the available modes.

              You can include other parameters as enrollment attributes for a
              specific course mode. For example, for credit mode, you can
              include the following parameters to specify the credit provider
              attribute.

              * namespace: credit
              * name: provider_id
              * value: institution_name

        **Example Requests**

            GET /api/enrollment/v1/enrollment

            POST /api/enrollment/v1/enrollment {

                "mode": "credit",
                "course_details":{"course_id": "edX/DemoX/Demo_Course"},
                "enrollment_attributes":[{"namespace": "credit","name": "provider_id","value": "hogwarts",},]

            }

            **POST Parameters**

              A POST request can include the following parameters.

              * user: Optional. The username of the currently logged in user.
                You cannot use the command to enroll a different user.

              * mode: Optional. The course mode for the enrollment. Individual
                users cannot upgrade their enrollment mode from 'honor'. Only
                server-to-server requests can enroll with other modes.

              * is_active: Optional. A Boolean value indicating whether the
                enrollment is active. Only server-to-server requests are
                allowed to deactivate an enrollment.

              * course details: A collection that includes the following
                information.

                  * course_id: The unique identifier for the course.

              * email_opt_in: Optional. A Boolean value that indicates whether
                the user wants to receive email from the organization that runs
                this course.

              * enrollment_attributes: A dictionary that contains the following
                values.

                  * namespace: Namespace of the attribute
                  * name: Name of the attribute
                  * value: Value of the attribute

              * is_active: Optional. A Boolean value that indicates whether the
                enrollment is active. Only server-to-server requests can
                deactivate an enrollment.

              * mode: Optional. The course mode for the enrollment. Individual
                users cannot upgrade their enrollment mode from "honor". Only
                server-to-server requests can enroll with other modes.

              * user: Optional. The user ID of the currently logged in user. You
                cannot use the command to enroll a different user.

        **GET Response Values**

            If an unspecified error occurs when the user tries to obtain a
            learner's enrollments, the request returns an HTTP 400 "Bad
            Request" response.

            If the user does not have permission to view enrollment data for
            the requested learner, the request returns an HTTP 404 "Not Found"
            response.

        **POST Response Values**

             If the user does not specify a course ID, the specified course
             does not exist, or the is_active status is invalid, the request
             returns an HTTP 400 "Bad Request" response.

             If a user who is not an admin tries to upgrade a learner's course
             mode, the request returns an HTTP 403 "Forbidden" response.

             If the specified user does not exist, the request returns an HTTP
             406 "Not Acceptable" response.

        **GET and POST Response Values**

            If the request is successful, an HTTP 200 "OK" response is
            returned along with a collection of course enrollments for the
            user or for the newly created enrollment.

            Each course enrollment contains the following values.

            * course_details: A collection that includes the following
              values.

                * course_end: The date and time when the course closes. If
                  null, the course never ends.

                * course_id: The unique identifier for the course.

                * course_modes: An array of data about the enrollment modes
                  supported for the course. If the request uses the parameter
                  include_expired=1, the array also includes expired
                  enrollment modes.

                  Each enrollment mode collection includes the following
                  values.

                  * currency: The currency of the listed prices.

                  * description: A description of this mode.

                  * expiration_datetime: The date and time after which users
                    cannot enroll in the course in this mode.

                  * min_price: The minimum price for which a user can enroll in
                    this mode.

                  * name: The full name of the enrollment mode.

                  * slug: The short name for the enrollment mode.

                  * suggested_prices: A list of suggested prices for this
                    enrollment mode.

                * course_start: The date and time when the course opens. If
                  null, the course opens immediately when it is created.

                * enrollment_end: The date and time after which users cannot
                  enroll for the course. If null, the enrollment period never
                  ends.

                * enrollment_start: The date and time when users can begin
                  enrolling in the course. If null, enrollment opens
                  immediately when the course is created.

                * invite_only: A value indicating whether students must be
                  invited to enroll in the course. Possible values are true or
                  false.

             * created: The date the user account was created.

             * is_active: Whether the enrollment is currently active.

             * mode: The enrollment mode of the user in this course.

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
        """Gets a list of all course enrollments for a user.

        Returns a list for the currently logged in user, or for the user named by the 'user' GET
        parameter. If the username does not match that of the currently logged in user, only
        courses for which the currently logged in user has the Staff or Admin role are listed.
        As a result, a course team member can find out which of his or her own courses a particular
        learner is enrolled in.

        Only the Staff or Admin role (granted on the Django administrative console as the staff
        or instructor permission) in individual courses gives the requesting user access to
        enrollment data. Permissions granted at the organizational level do not give a user
        access to enrollment data for all of that organization's courses.

        Users who have the global staff permission can access all enrollment data for all
        courses.
        """
        username = request.GET.get('user', request.user.username)
        try:
            enrollment_data = api.get_enrollments(username)
        except CourseEnrollmentError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"An error occurred while retrieving enrollments for user '{username}'"
                    ).format(username=username)
                }
            )
        if username == request.user.username or GlobalStaff().has_user(request.user) or \
                self.has_api_key_permissions(request):
            return Response(enrollment_data)
        filtered_data = []
        for enrollment in enrollment_data:
            course_key = CourseKey.from_string(enrollment["course_details"]["course_id"])
            if user_has_role(request.user, CourseStaffRole(course_key)):
                filtered_data.append(enrollment)
        return Response(filtered_data)

    def post(self, request):
        """Enrolls the currently logged-in user in a course.

        Server-to-server calls may deactivate or modify the mode of existing enrollments. All other requests
        go through `add_enrollment()`, which allows creation of new and reactivation of old enrollments.
        """
        # Get the User, Course ID, and Mode from the request.

        username = request.data.get('user', request.user.username)
        course_id = request.data.get('course_details', {}).get('course_id')

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

        mode = request.data.get('mode', CourseMode.HONOR)

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
            is_active = request.data.get('is_active')
            # Check if the requested activation status is None or a Boolean
            if is_active is not None and not isinstance(is_active, bool):
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        'message': (u"'{value}' is an invalid enrollment activation status.").format(value=is_active)
                    }
                )

            enrollment_attributes = request.data.get('enrollment_attributes')
            enrollment = api.get_enrollment(username, unicode(course_id))
            mode_changed = enrollment and mode is not None and enrollment['mode'] != mode
            active_changed = enrollment and is_active is not None and enrollment['is_active'] != is_active
            missing_attrs = []
            if enrollment_attributes:
                actual_attrs = [
                    u"{namespace}:{name}".format(**attr)
                    for attr in enrollment_attributes
                ]
                missing_attrs = set(REQUIRED_ATTRIBUTES.get(mode, [])) - set(actual_attrs)
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

                if len(missing_attrs) > 0:
                    msg = u"Missing enrollment attributes: requested mode={} required attributes={}".format(
                        mode, REQUIRED_ATTRIBUTES.get(mode)
                    )
                    log.warning(msg)
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": msg})

                response = api.update_enrollment(
                    username,
                    unicode(course_id),
                    mode=mode,
                    is_active=is_active,
                    enrollment_attributes=enrollment_attributes
                )
            else:
                # Will reactivate inactive enrollments.
                response = api.add_enrollment(username, unicode(course_id), mode=mode, is_active=is_active)

            email_opt_in = request.data.get('email_opt_in', None)
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
                    ).format(mode=mode, course_id=course_id),
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
