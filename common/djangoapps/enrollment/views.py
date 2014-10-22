"""
The Enrollment API Views should be simple, lean HTTP endpoints for API access. This should
consist primarily of authentication, request validation, and serialization.

"""
from rest_framework import status
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from enrollment import api
from student.models import NonExistentCourseError, CourseEnrollmentException


class EnrollmentUserThrottle(UserRateThrottle):
        rate = '50/second'  # TODO Limit significantly after performance testing.


@api_view(['GET'])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
@throttle_classes([EnrollmentUserThrottle])
def list_student_enrollments(request):
    """List out all the enrollments for the current student

    Returns a JSON response with all the course enrollments for the current student.

    Args:
        request (Request): The GET request for course enrollment listings.

    Returns:
        A JSON serialized representation of the student's course enrollments.

    """
    return Response(api.get_enrollments(request.user.username))


@api_view(['GET', 'POST'])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
@throttle_classes([EnrollmentUserThrottle])
def get_course_enrollment(request, course_id=None):
    """Create, read, or update enrollment information for a student.

    HTTP Endpoint for all CRUD operations for a student course enrollment. Allows creation, reading, and
    updates of the current enrollment for a particular course.

    Args:
        request (Request): To get current course enrollment information, a GET request will return
            information for the current user and the specified course. A POST request will create a
            new course enrollment for the current user. If 'mode' or 'deactivate' are found in the
            POST parameters, the mode can be modified, or the enrollment can be deactivated.
        course_id (str): URI element specifying the course location. Enrollment information will be
            returned, created, or updated for this particular course.

    Return:
        A JSON serialized representation of the course enrollment. If this is a new or modified enrollment,
        the returned enrollment will reflect all changes.

    """
    try:
        if 'mode' in request.DATA:
            return Response(api.update_enrollment(request.user.username, course_id, request.DATA['mode']))
        elif 'deactivate' in request.DATA:
            return Response(api.deactivate_enrollment(request.user.username, course_id))
        elif course_id and request.method == 'POST':
            return Response(api.add_enrollment(request.user.username, course_id))
        else:
            return Response(api.get_enrollment(request.user.username, course_id))
    except api.CourseModeNotFoundError as error:
        return Response(status=status.HTTP_400_BAD_REQUEST, data=error.data)
    except NonExistentCourseError:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except api.EnrollmentNotFoundError:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except CourseEnrollmentException:
        return Response(status=status.HTTP_400_BAD_REQUEST)
