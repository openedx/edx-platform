"""
The Enrollment API Views should be simple, lean HTTP endpoints for API access. This should
consist primarily of authentication, request validation, and serialization.

"""
from rest_framework import status
from rest_framework.authentication import OAuth2Authentication
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from enrollment import api
from enrollment.errors import CourseNotFoundError, CourseEnrollmentError, CourseModeNotFoundError
from util.authentication import SessionAuthenticationAllowInactiveUser


class EnrollmentUserThrottle(UserRateThrottle):
    """Limit the number of requests users can make to the enrollment API."""
    # TODO Limit significantly after performance testing.  # pylint: disable=fixme
    rate = '50/second'


class EnrollmentView(APIView):
    """ Enrollment API View for creating, updating, and viewing course enrollments. """

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


class EnrollmentCourseDetailView(APIView):
    """ Enrollment API View for viewing course enrollment details. """

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


class EnrollmentListView(APIView):
    """ Enrollment API List View for viewing all course enrollments for a user. """

    authentication_classes = OAuth2Authentication, SessionAuthenticationAllowInactiveUser
    permission_classes = permissions.IsAuthenticated,
    throttle_classes = EnrollmentUserThrottle,

    def get(self, request):
        """List out all the enrollments for the current user

        Returns a JSON response with all the course enrollments for the current user.

        Args:
            request (Request): The GET request for course enrollment listings.
            user (str): Get all enrollments for the specified user's username.

        Returns:
            A JSON serialized representation of the user's course enrollments.

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
        """Create a new enrollment

        Creates a new enrollment based on the data posted. Currently all that can be specified is
        the course id.  All other attributes will be determined by the server, and cannot be updated
        through this endpoint.

        By default, this will attempt to create the enrollment with course mode 'honor'. If the course
        does not have an 'honor' course mode, it will fail as a bad request and list the available
        course modes.

        Args:
            request (Request): The POST request to create a new enrollment. POST DATA should contain
                'course_details' with an attribute 'course_id' to identify which course to enroll in.
                'user' may be specified as well, but must match the username of the authenticated user.
                Ex. {'user': 'Bob', 'course_details': { 'course_id': 'edx/demo/T2014' } }

        Returns:
            A JSON serialized representation of the user's new course enrollment.

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
