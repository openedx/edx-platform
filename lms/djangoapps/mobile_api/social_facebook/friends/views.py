"""
    Views for friends info API
"""

from rest_framework import generics, status
from rest_framework.response import Response
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment
from ...utils import mobile_view
from ..utils import get_friends_from_facebook, get_linked_edx_accounts, share_with_facebook_friends
from lms.djangoapps.mobile_api.social_facebook.friends import serializers


@mobile_view()
class FriendsInCourse(generics.ListAPIView):
    """
    **Use Case**

        API endpoint that returns all the users friends that are in the course specified.
        Note that only friends that allow their courses to be shared will be included.

    **Example request**:

        GET /api/mobile/v0.5/social/facebook/friends/course/<course_id>

        where course_id is in the form of /edX/DemoX/Demo_Course

    **Response Values**

        {
            "friends": [
                {
                    "name": "test",
                    "id": "12345",
                },
                ...
            ]
        }
    """
    serializer_class = serializers.FriendsInCourseSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.GET, files=request.FILES)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get all the user's FB friends
        result = get_friends_from_facebook(serializer)
        if not isinstance(result, list):
            return result

        def is_member(friend, course_key):
            """
            Return true if friend is a member of the course specified by the course_key
            """
            return CourseEnrollment.objects.filter(
                course_id=course_key,
                user_id=friend['edX_id']
            ).count() == 1

        # For each friend check if they are a linked edX user
        friends_with_edx_users = get_linked_edx_accounts(result)

        # Filter by sharing preferences and enrollment in course
        course_key = CourseKey.from_string(kwargs['course_id'])
        friends_with_sharing_in_course = [
            {'id': friend['id'], 'name': friend['name']}
            for friend in friends_with_edx_users
            if share_with_facebook_friends(friend) and is_member(friend, course_key)
        ]
        return Response({'friends': friends_with_sharing_in_course})
