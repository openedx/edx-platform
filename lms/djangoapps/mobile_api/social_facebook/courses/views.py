"""
    Views for courses info API
"""

from rest_framework import generics, status
from rest_framework.response import Response
from courseware.access import is_mobile_available_for_user
from student.models import CourseEnrollment
from lms.djangoapps.mobile_api.social_facebook.courses import serializers
from ...users.serializers import CourseEnrollmentSerializer
from ...utils import mobile_view
from ..utils import get_friends_from_facebook, get_linked_edx_accounts, share_with_facebook_friends


@mobile_view()
class CoursesWithFriends(generics.ListAPIView):
    """
    **Use Case**

        API endpoint for retrieving all the courses that a user's friends are in.
        Note that only friends that allow their courses to be shared will be included.

    **Example request**

        GET /api/mobile/v0.5/social/facebook/courses/friends

    **Response Values**

        See UserCourseEnrollmentsList in lms/djangoapps/mobile_api/users for the structure of the response values.
    """
    serializer_class = serializers.CoursesWithFriendsSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.GET, files=request.FILES)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get friends from Facebook
        result = get_friends_from_facebook(serializer)
        if not isinstance(result, list):
            return result

        friends_that_are_edx_users = get_linked_edx_accounts(result)

        # Filter by sharing preferences
        users_with_sharing = [
            friend for friend in friends_that_are_edx_users if share_with_facebook_friends(friend)
        ]

        # Get unique enrollments
        enrollments = []
        for friend in users_with_sharing:
            query_set = CourseEnrollment.objects.filter(
                user_id=friend['edX_id']
            ).exclude(course_id__in=[enrollment.course_id for enrollment in enrollments])
            enrollments.extend(query_set)

        # Get course objects
        courses = [
            enrollment for enrollment in enrollments if enrollment.course
            and is_mobile_available_for_user(self.request.user, enrollment.course)
        ]

        return Response(CourseEnrollmentSerializer(courses, context={'request': request}).data)
