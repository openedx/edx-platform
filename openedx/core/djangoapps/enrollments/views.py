"""
The Enrollment API Views should be simple, lean HTTP endpoints for API access. This should
consist primarily of authentication, request validation, and serialization.

"""


import logging

from six import text_type

from common.djangoapps.course_modes.models import CourseMode
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.decorators import method_decorator
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.core.djangoapps.cors_csrf.decorators import ensure_csrf_cookie_cross_domain
from openedx.core.djangoapps.course_groups.cohorts import CourseUserGroup, add_user_to_cohort, get_cohort_by_name
from openedx.core.djangoapps.embargo import api as embargo_api
from openedx.core.djangoapps.enrollments import api
from openedx.core.djangoapps.enrollments.errors import (
    CourseEnrollmentError, CourseEnrollmentExistsError, CourseModeNotFoundError,
)
from openedx.core.djangoapps.enrollments.forms import CourseEnrollmentsApiListForm
from openedx.core.djangoapps.enrollments.paginators import CourseEnrollmentsApiListPagination
from openedx.core.djangoapps.enrollments.serializers import CourseEnrollmentsApiListSerializer
from openedx.core.djangoapps.user_api.accounts.permissions import CanRetireUser
from openedx.core.djangoapps.user_api.models import UserRetirementStatus
from openedx.core.djangoapps.user_api.preferences.api import update_email_opt_in
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission, ApiKeyHeaderPermissionIsAuthenticated
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from openedx.core.lib.exceptions import CourseNotFoundError
from openedx.core.lib.log_utils import audit_log
from openedx.features.enterprise_support.api import (
    ConsentApiServiceClient,
    EnterpriseApiException,
    EnterpriseApiServiceClient,
    enterprise_enabled
)
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from common.djangoapps.student.auth import user_has_role
from common.djangoapps.student.models import CourseEnrollment, User
from common.djangoapps.student.roles import CourseStaffRole, GlobalStaff
from common.djangoapps.util.disable_rate_limit import can_disable_rate_limit

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

    # To see how the staff rate limit was selected, see https://github.com/edx/edx-platform/pull/18360
    THROTTLE_RATES = {
        'user': '40/minute',
        'staff': '120/minute',
    }

    def allow_request(self, request, view):
        # Use a special scope for staff to allow for a separate throttle rate
        user = request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            self.scope = 'staff'
            self.rate = self.get_rate()
            self.num_requests, self.duration = self.parse_rate(self.rate)

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
                * course_name: The name of the course.
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

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)
    throttle_classes = (EnrollmentUserThrottle,)

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
                and not request.user.is_staff:
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


class EnrollmentUserRolesView(APIView):
    """
    **Use Case**

        Get the roles for the current logged-in user.
        A field is also included to indicate whether or not the user is a global
        staff member.
        If an optional course_id parameter is supplied, the returned roles will be
        filtered to only include roles for the given course.

    **Example Requests**

        GET /api/enrollment/v1/roles/?course_id={course_id}

        course_id: (optional) A course id. The returned roles will be filtered to
        only include roles for the given course.

    **Response Values**

        If the request is successful, an HTTP 200 "OK" response is
        returned along with a collection of user roles for the
        logged-in user, filtered by course_id if given, along with
        whether or not the user is global staff
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        EnrollmentCrossDomainSessionAuth,
    )
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)
    throttle_classes = (EnrollmentUserThrottle,)

    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request):
        """
        Gets a list of all roles for the currently logged-in user, filtered by course_id if supplied
        """
        try:
            course_id = request.GET.get('course_id')
            roles_data = api.get_user_roles(request.user.username)
            if course_id:
                roles_data = [role for role in roles_data if text_type(role.course_id) == course_id]
        except Exception:  # pylint: disable=broad-except
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"An error occurred while retrieving roles for user '{username}"
                    ).format(username=request.user.username)
                }
            )
        return Response({
            'roles': [
                {
                    "org": role.org,
                    "course_id": text_type(role.course_id),
                    "role": role.role
                }
                for role in roles_data],
            'is_staff': request.user.is_staff,
        })


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
                * course_name: The name of the course.
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
    throttle_classes = (EnrollmentUserThrottle,)

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


class UnenrollmentView(APIView):
    """
        **Use Cases**

            * Unenroll a single user from all courses.

              This command can only be issued by a privileged service user.

        **Example Requests**

            POST /api/enrollment/v1/enrollment {
                "username": "username12345"
            }

        **POST Parameters**

            A POST request must include the following parameter.

            * username: The username of the user being unenrolled.
            This will never match the username from the request,
            since the request is issued as a privileged service user.

        **POST Response Values**

            If the user has not requested retirement and does not have a retirement
            request status, the request returns an HTTP 404 "Does Not Exist" response.

            If the user is already unenrolled from all courses, the request returns
            an HTTP 204 "No Content" response.

            If an unexpected error occurs, the request returns an HTTP 500 response.

            If the request is successful, an HTTP 200 "OK" response is
            returned along with a list of all courses from which the user was unenrolled.
        """
    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated, CanRetireUser,)

    def post(self, request):
        """
        Unenrolls the specified user from all courses.
        """
        try:
            # Get the username from the request.
            username = request.data['username']
            # Ensure that a retirement request status row exists for this username.
            UserRetirementStatus.get_retirement_for_retirement_action(username)
            enrollments = api.get_enrollments(username)
            active_enrollments = [enrollment for enrollment in enrollments if enrollment['is_active']]
            if len(active_enrollments) < 1:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(api.unenroll_user_from_all_courses(username))
        except KeyError:
            return Response(u'Username not specified.', status=status.HTTP_404_NOT_FOUND)
        except UserRetirementStatus.DoesNotExist:
            return Response(u'No retirement request status for username.', status=status.HTTP_404_NOT_FOUND)
        except Exception as exc:  # pylint: disable=broad-except
            return Response(text_type(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@can_disable_rate_limit
class EnrollmentListView(APIView, ApiKeyPermissionMixIn):
    """
        **Use Cases**

            * Get a list of all course enrollments for the currently signed in user.

            * Enroll the currently signed in user in a course.

              Currently a user can use this command only to enroll the
              user in the default course mode. If this is not
              supported for the course, the request fails and returns
              the available modes.

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
                users cannot upgrade their enrollment mode from the default. Only
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
                users cannot upgrade their enrollment mode from the default. Only
                server-to-server requests can enroll with other modes.

              * user: Optional. The user ID of the currently logged in user. You
                cannot use the command to enroll a different user.

              * enterprise_course_consent: Optional. A Boolean value that
                indicates the consent status for an EnterpriseCourseEnrollment
                to be posted to the Enterprise service.

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

                * course_name: The name of the course.

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
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        EnrollmentCrossDomainSessionAuth,
    )
    permission_classes = (ApiKeyHeaderPermissionIsAuthenticated,)
    throttle_classes = (EnrollmentUserThrottle,)

    # Since the course about page on the marketing site
    # uses this API to auto-enroll users, we need to support
    # cross-domain CSRF.
    @method_decorator(ensure_csrf_cookie_cross_domain)
    def get(self, request):
        """Gets a list of all course enrollments for a user.

        Returns a list for the currently logged in user, or for the user named by the 'user' GET
        parameter. If the username does not match that of the currently logged in user, only
        courses for which the currently logged in user has the Staff or Admin role are listed.
        As a result, a course team member can find out which of their own courses a particular
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
        # pylint: disable=too-many-statements
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

        mode = request.data.get('mode')

        has_api_key_permissions = self.has_api_key_permissions(request)

        # Check that the user specified is either the same user, or this is a server-to-server request.
        if not username:
            username = request.user.username
        if username != request.user.username and not has_api_key_permissions \
                and not GlobalStaff().has_user(request.user):
            # Return a 404 instead of a 403 (Unauthorized). If one user is looking up
            # other users, do not let them deduce the existence of an enrollment.
            return Response(status=status.HTTP_404_NOT_FOUND)

        if mode not in (CourseMode.AUDIT, CourseMode.HONOR, None) and not has_api_key_permissions \
                and not GlobalStaff().has_user(request.user):
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

            explicit_linked_enterprise = request.data.get('linked_enterprise_customer')
            if explicit_linked_enterprise and has_api_key_permissions and enterprise_enabled():
                enterprise_api_client = EnterpriseApiServiceClient()
                consent_client = ConsentApiServiceClient()
                try:
                    enterprise_api_client.post_enterprise_course_enrollment(username, text_type(course_id), None)
                except EnterpriseApiException as error:
                    log.exception(u"An unexpected error occurred while creating the new EnterpriseCourseEnrollment "
                                  u"for user [%s] in course run [%s]", username, course_id)
                    raise CourseEnrollmentError(text_type(error))
                kwargs = {
                    'username': username,
                    'course_id': text_type(course_id),
                    'enterprise_customer_uuid': explicit_linked_enterprise,
                }
                consent_client.provide_consent(**kwargs)

            enrollment_attributes = request.data.get('enrollment_attributes')
            enrollment = api.get_enrollment(username, text_type(course_id))
            mode_changed = enrollment and mode is not None and enrollment['mode'] != mode
            active_changed = enrollment and is_active is not None and enrollment['is_active'] != is_active
            missing_attrs = []
            if enrollment_attributes:
                actual_attrs = [
                    u"{namespace}:{name}".format(**attr)
                    for attr in enrollment_attributes
                ]
                missing_attrs = set(REQUIRED_ATTRIBUTES.get(mode, [])) - set(actual_attrs)
            if (GlobalStaff().has_user(request.user) or has_api_key_permissions) and (mode_changed or active_changed):
                if mode_changed and active_changed and not is_active:
                    # if the requester wanted to deactivate but specified the wrong mode, fail
                    # the request (on the assumption that the requester had outdated information
                    # about the currently active enrollment).
                    msg = u"Enrollment mode mismatch: active mode={}, requested mode={}. Won't deactivate.".format(
                        enrollment["mode"], mode
                    )
                    log.warning(msg)
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": msg})

                if missing_attrs:
                    msg = u"Missing enrollment attributes: requested mode={} required attributes={}".format(
                        mode, REQUIRED_ATTRIBUTES.get(mode)
                    )
                    log.warning(msg)
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": msg})

                response = api.update_enrollment(
                    username,
                    text_type(course_id),
                    mode=mode,
                    is_active=is_active,
                    enrollment_attributes=enrollment_attributes,
                    # If we are updating enrollment by authorized api caller, we should allow expired modes
                    include_expired=has_api_key_permissions
                )
            else:
                # Will reactivate inactive enrollments.
                response = api.add_enrollment(
                    username,
                    text_type(course_id),
                    mode=mode,
                    is_active=is_active,
                    enrollment_attributes=enrollment_attributes
                )

            cohort_name = request.data.get('cohort')
            if cohort_name is not None:
                cohort = get_cohort_by_name(course_id, cohort_name)
                try:
                    add_user_to_cohort(cohort, user)
                except ValueError:
                    # user already in cohort, probably because they were un-enrolled and re-enrolled
                    log.exception('Cohort re-addition')
            email_opt_in = request.data.get('email_opt_in', None)
            if email_opt_in is not None:
                org = course_id.org
                update_email_opt_in(request.user, org, email_opt_in)

            log.info(u'The user [%s] has already been enrolled in course run [%s].', username, course_id)
            ## EOL
            try:
                from welcome_mail.views import send_email
                send_email(user.email, course_id)
            except Exception as e:
                log.error('WelcomeMail - Error to send_email(), error: {}'.format(str(e)))
            ## END EOL
            return Response(response)
        except CourseModeNotFoundError as error:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"The [{mode}] course mode is expired or otherwise unavailable for course run [{course_id}]."
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
            log.warning(u'An enrollment already exists for user [%s] in course run [%s].', username, course_id)
            return Response(data=error.enrollment)
        except CourseEnrollmentError:
            log.exception(u"An error occurred while creating the new course enrollment for user "
                          u"[%s] in course run [%s]", username, course_id)
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"An error occurred while creating the new course enrollment for user "
                        u"'{username}' in course '{course_id}'"
                    ).format(username=username, course_id=course_id)
                }
            )
        except CourseUserGroup.DoesNotExist:
            log.exception(u'Missing cohort [%s] in course run [%s]', cohort_name, course_id)
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": u"An error occured while adding to cohort [%s]" % cohort_name
                })
        finally:
            # Assumes that the ecommerce service uses an API key to authenticate.
            if has_api_key_permissions:
                current_enrollment = api.get_enrollment(username, text_type(course_id))
                audit_log(
                    'enrollment_change_requested',
                    course_id=text_type(course_id),
                    requested_mode=mode,
                    actual_mode=current_enrollment['mode'] if current_enrollment else None,
                    requested_activation=is_active,
                    actual_activation=current_enrollment['is_active'] if current_enrollment else None,
                    user_id=user.id
                )


@can_disable_rate_limit
class CourseEnrollmentsApiListView(DeveloperErrorViewMixin, ListAPIView):
    """
        **Use Cases**

            Get a list of all course enrollments, optionally filtered by a course ID or list of usernames.

        **Example Requests**

            GET /api/enrollment/v1/enrollments

            GET /api/enrollment/v1/enrollments?course_id={course_id}

            GET /api/enrollment/v1/enrollments?username={username},{username},{username}

            GET /api/enrollment/v1/enrollments?course_id={course_id}&username={username}

        **Query Parameters for GET**

            * course_id: Filters the result to course enrollments for the course corresponding to the
              given course ID. The value must be URL encoded. Optional.

            * username: List of comma-separated usernames. Filters the result to the course enrollments
              of the given users. Optional.

            * page_size: Number of results to return per page. Optional.

            * page: Page number to retrieve. Optional.

        **Response Values**

            If the request for information about the course enrollments is successful, an HTTP 200 "OK" response
            is returned.

            The HTTP 200 response has the following values.

            * results: A list of the course enrollments matching the request.

                * created: Date and time when the course enrollment was created.

                * mode: Mode for the course enrollment.

                * is_active: Whether the course enrollment is active or not.

                * user: Username of the user in the course enrollment.

                * course_id: Course ID of the course in the course enrollment.

            * next: The URL to the next page of results, or null if this is the
              last page.

            * previous: The URL to the next page of results, or null if this
              is the first page.

            If the user is not logged in, a 401 error is returned.

            If the user is not global staff, a 403 error is returned.

            If the specified course_id is not valid or any of the specified usernames
            are not valid, a 400 error is returned.

            If the specified course_id does not correspond to a valid course or if all the specified
            usernames do not correspond to valid users, an HTTP 200 "OK" response is returned with an
            empty 'results' field.
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAdminUser,)
    throttle_classes = (EnrollmentUserThrottle,)
    serializer_class = CourseEnrollmentsApiListSerializer
    pagination_class = CourseEnrollmentsApiListPagination

    def get_queryset(self):
        """
        Get all the course enrollments for the given course_id and/or given list of usernames.
        """
        form = CourseEnrollmentsApiListForm(self.request.query_params)

        if not form.is_valid():
            raise ValidationError(form.errors)

        queryset = CourseEnrollment.objects.all()
        course_id = form.cleaned_data.get('course_id')
        usernames = form.cleaned_data.get('username')

        if course_id:
            queryset = queryset.filter(course_id=course_id)
        if usernames:
            queryset = queryset.filter(user__username__in=usernames)
        return queryset
