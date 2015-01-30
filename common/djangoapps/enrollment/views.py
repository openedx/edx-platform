"""
The Enrollment API Views should be simple, lean HTTP endpoints for API access. This should
consist primarily of authentication, request validation, and serialization.

"""
from opaque_keys import InvalidKeyError
from rest_framework import status
from rest_framework.authentication import OAuth2Authentication
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from enrollment import api
from enrollment.errors import CourseNotFoundError, CourseEnrollmentError, CourseModeNotFoundError
from util.authentication import SessionAuthenticationAllowInactiveUser
from util.disable_rate_limit import can_disable_rate_limit


class EnrollmentUserThrottle(UserRateThrottle):
    """Limit the number of requests users can make to the enrollment API."""
    # TODO Limit significantly after performance testing.  # pylint: disable=fixme
    rate = '50/second'


@can_disable_rate_limit
class EnrollmentView(APIView):
    """
        **Use Cases**

            Get the user's enrollment status for a course.

        **Example Requests**:

            GET /api/enrollment/v1/enrollment/{user_id},{course_id}

        **Response Values**

            * created: The date the user account was created.

            * mode: The enrollment mode of the user in this course.

            * is_active: Whether the enrollment is currently active.

            * course_details: A collection that includes:

                * course_id: The unique identifier for the course.

                * enrollment_end: The date and time after which users cannot enroll for the course.

                * course_modes: An array of data about the enrollment modes supported for the course. Each enrollment mode collection includes:

                    * slug: The short name for the enrollment mode.
                    * name: The full name of the enrollment mode.
                    * min_price: The minimum price for which a user can enroll in this mode.
                    * suggested_prices: A list of suggested prices for this enrollment mode.
                    * currency: The currency of the listed prices.
                    * expiration_datetime: The date and time after which users cannot enroll in the course in this mode.
                    * description: A description of this mode.

                * enrollment_start: The date and time that users can begin enrolling in the course.

                * invite_only: Whether students must be invited to enroll in the course; true or false.

            * user: The ID of the user.
    """

    authentication_classes = OAuth2Authentication, SessionAuthenticationAllowInactiveUser
    permission_classes = permissions.IsAuthenticated,
    throttle_classes = EnrollmentUserThrottle,

    def get(self, request, course_id=None, user=None):
        """Create, read, or update enrollment information for a user.

        HTTP Endpoint for all CRUD operations for a user course enrollment. Allows creation, reading, and
        updates of the current enrollment for a particular course.

        Args:
            request (Request): To get current course enrollment information, a GET request will return
                information for the current user and the specified course.
            course_id (str): URI element specifying the course location. Enrollment information will be
                returned, created, or updated for this particular course.
            user (str): The user username associated with this enrollment request.

        Return:
            A JSON serialized representation of the course enrollment.

        """
        user = user if user else request.user.username
        if request.user.username != user:
            # Return a 404 instead of a 403 (Unauthorized). If one user is looking up
            # other users, do not let them deduce the existence of an enrollment.
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            return Response(api.get_enrollment(user, course_id))
        except CourseEnrollmentError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"An error occurred while retrieving enrollments for user "
                        u"'{user}' in course '{course_id}'"
                    ).format(user=user, course_id=course_id)
                }
            )


@can_disable_rate_limit
class EnrollmentCourseDetailView(APIView):
    """
        **Use Cases**

            Get enrollment details for a course.

            **Note:** Getting enrollment details for a course does not require authentication.

        **Example Requests**:

            GET /api/enrollment/v1/course/{course_id}


        **Response Values**

            A collection of course enrollments for the user, or for the newly created enrollment. Each course enrollment contains:

                * course_id: The unique identifier of the course.

                * enrollment_end: The date and time after which users cannot enroll for the course.

                * course_modes: An array of data about the enrollment modes supported for the course. Each enrollment mode collection includes:

                        * slug: The short name for the enrollment mode.
                        * name: The full name of the enrollment mode.
                        * min_price: The minimum price for which a user can enroll in this mode.
                        * suggested_prices: A list of suggested prices for this enrollment mode.
                        * currency: The currency of the listed prices.
                        * expiration_datetime: The date and time after which users cannot enroll in the course in this mode.
                        * description: A description of this mode.

                * enrollment_start: The date and time that users can begin enrolling in the course.

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
            return Response(api.get_course_enrollment_details(course_id))
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
class EnrollmentListView(APIView):
    """
        **Use Cases**

            1. Get a list of all course enrollments for the currently logged in user.

            2. Enroll the currently logged in user in a course.

               Currently you can use this command only to enroll the user in "honor" mode.

               If honor mode is not supported for the course, the request fails and returns the available modes.

        **Example Requests**:

            GET /api/enrollment/v1/enrollment

            POST /api/enrollment/v1/enrollment{"course_details":{"course_id": "edX/DemoX/Demo_Course"}}

        **Post Parameters**

            * user:  The user ID of the currently logged in user. Optional. You cannot use the command to enroll a different user.

            * course details: A collection that contains:

                * course_id: The unique identifier for the course.

        **Response Values**

            A collection of course enrollments for the user, or for the newly created enrollment. Each course enrollment contains:

                * created: The date the user account was created.

                * mode: The enrollment mode of the user in this course.

                * is_active: Whether the enrollment is currently active.

                * course_details: A collection that includes:

                    * course_id:  The unique identifier for the course.

                    * enrollment_end: The date and time after which users cannot enroll for the course.

                    * course_modes: An array of data about the enrollment modes supported for the course. Each enrollment mode collection includes:

                        * slug: The short name for the enrollment mode.
                        * name: The full name of the enrollment mode.
                        * min_price: The minimum price for which a user can enroll in this mode.
                        * suggested_prices: A list of suggested prices for this enrollment mode.
                        * currency: The currency of the listed prices.
                        * expiration_datetime: The date and time after which users cannot enroll in the course in this mode.
                        * description: A description of this mode.

                    * enrollment_start: The date and time that users can begin enrolling in the course.

                    * invite_only: Whether students must be invited to enroll in the course; true or false.

                * user: The ID of the user.
    """

    authentication_classes = OAuth2Authentication, SessionAuthenticationAllowInactiveUser
    permission_classes = permissions.IsAuthenticated,
    throttle_classes = EnrollmentUserThrottle,

    def get(self, request):
        """
            Gets a list of all course enrollments for the currently logged in user.
        """
        user = request.GET.get('user', request.user.username)
        if request.user.username != user:
            # Return a 404 instead of a 403 (Unauthorized). If one user is looking up
            # other users, do not let them deduce the existence of an enrollment.
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            return Response(api.get_enrollments(user))
        except CourseEnrollmentError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"An error occurred while retrieving enrollments for user '{user}'"
                    ).format(user=user)
                }
            )

    def post(self, request):
        """
            Enrolls the currently logged in user in a course.
        """
        user = request.DATA.get('user', request.user.username)
        if not user:
            user = request.user.username
        if user != request.user.username:
            # Return a 404 instead of a 403 (Unauthorized). If one user is looking up
            # other users, do not let them deduce the existence of an enrollment.
            return Response(status=status.HTTP_404_NOT_FOUND)

        if 'course_details' not in request.DATA or 'course_id' not in request.DATA['course_details']:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": u"Course ID must be specified to create a new enrollment."}
            )
        course_id = request.DATA['course_details']['course_id']

        try:
            return Response(api.add_enrollment(user, course_id))
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
        except CourseEnrollmentError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"An error occurred while creating the new course enrollment for user "
                        u"'{user}' in course '{course_id}'"
                    ).format(user=user, course_id=course_id)
                }
            )
        except InvalidKeyError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": u"No course '{course_id}' found for enrollment".format(course_id=course_id)
                }
            )
