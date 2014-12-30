"""
Implementation of the RESTful endpoints for the Course About API.

"""
from opaque_keys import InvalidKeyError
from rest_framework import permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from course_about import api
from rest_framework import status
from rest_framework.response import Response
from course_about.errors import CourseNotFoundError


class CourseAboutThrottle(UserRateThrottle):
    """Limit the number of requests users can make to the Course About API."""
    # TODO Limit based on expected throughput  # pylint: disable=fixme
    rate = '50/second'


class CourseAboutView(APIView):
    """ RESTful Course About API view.

    Used to retrieve JSON serialized Course About information.

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = CourseAboutThrottle,

    def get(self, request, course_id=None):  # pylint: disable=unused-argument
        """read course information.

        HTTP Endpoint for course info api.

        Args:
            Course Id = URI element specifying the course location. Course information will be
                returned for this particular course.

        Return:
            A JSON serialized representation of the course information

        """
        try:
            return Response(api.get_course_about_details(course_id))
        except InvalidKeyError:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={
                    "message": (
                        u"Course '{course_id}' not found."
                    ).format(course_id=course_id)
                }
            )
        except CourseNotFoundError:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={
                    "message": (
                        u"An error occurred while retrieving course information"
                        u" for course '{course_id}' no course found"
                    ).format(course_id=course_id)
                }
            )
        except:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": (
                        u"An error occurred while retrieving course information"
                        u" for course '{course_id}'"
                    ).format(course_id=course_id)
                }
            )
