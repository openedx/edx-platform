"""
    Views for friends info API
"""

from rest_framework import generics, status
from rest_framework.response import Response
from openedx.core.djangoapps.user_api.api.profile import preference_info
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment
from ...utils import mobile_view
from ..utils import get_friends_from_facebook, get_linked_edx_accounts, share_with_facebook_friends
from lms.djangoapps.mobile_api.social_facebook.friends import serializers
from django.conf import settings

_FACEBOOK_API_VERSION = settings.FACEBOOK_API_VERSION


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

        {   "friends":
                [{
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
        if serializer.is_valid():
            # Get all the users FB friends
            result = get_friends_from_facebook(serializer)
            if type(result) == list:
                # For each friend check if they are a linked edX user
                friends_with_edx_users = get_linked_edx_accounts(result)
                # Filter by sharing preferences
                friends_with_edx_users_sharing = [
                    friend for friend in friends_with_edx_users if share_with_facebook_friends(friend)
                ]
                course_key = CourseKey.from_string(kwargs['course_id'])
                fb_friends_in_course = [
                    friend for friend in friends_with_edx_users_sharing if self.is_member(course_key, friend)
                ]
                fb_friends_in_course = map(remove_edx_id_and_username, fb_friends_in_course)
                return Response({'friends': fb_friends_in_course})
            else:
                return result
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def is_member(self, course_key, friend):
        '''
            Return true if friend is a member of the course
            specified by the course_key
        '''
        return CourseEnrollment.objects.filter(
            course_id=course_key,
            user_id=friend['edX_id'],
            is_active=True
        ).count() == 1


def remove_edx_id_and_username(friend):
    '''
        Remove the edx course id and and the edX username
        from the friend object
    '''
    try:
        del friend['edX_id']
        del friend['edX_username']
    except KeyError:
        pass
    return friend
