"""
Course Goals Views - includes REST API
"""


from django.contrib.auth import get_user_model
from django.http import JsonResponse
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from lms.djangoapps.course_goals.api import get_course_goal_options
from lms.djangoapps.course_goals.models import GOAL_KEY_CHOICES, CourseGoal, UserActivity
from openedx.core.lib.api.permissions import IsStaffOrOwner

User = get_user_model()


class CourseGoalSerializer(serializers.ModelSerializer):
    """
    Serializes CourseGoal models.
    """
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = CourseGoal
        fields = ('user', 'course_key', 'goal_key')


class CourseGoalViewSet(viewsets.ModelViewSet):
    """
    API calls to create and update a course goal.

    Validates incoming data to ensure that course_key maps to an actual
    course and that the goal_key is a valid option.

    **Use Case**
        * Create a new goal for a user.
        * Update an existing goal for a user

    **Example Requests**
        POST /api/course_goals/v0/course_goals/
            Request data: {"course_key": <course-key>, "goal_key": "<goal-key>", "user": "<username>"}

    Returns Http400 response if the course_key does not map to a known
    course or if the goal_key does not map to a valid goal key.
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsStaffOrOwner,)
    queryset = CourseGoal.objects.all()
    serializer_class = CourseGoalSerializer

    # Another version of this endpoint exists in ../course_home_api/outline/views.py
    # This version is used by the legacy frontend and is deprecated
    def create(self, post_data):  # lint-amnesty, pylint: disable=arguments-differ
        """ Create a new goal if one does not exist, otherwise update the existing goal. """
        # Ensure goal_key is valid
        goal_options = get_course_goal_options()
        goal_key = post_data.data.get('goal_key')
        if not goal_key:
            return Response(
                'Please provide a valid goal key from following options. (options= {goal_options}).'.format(
                    goal_options=goal_options,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif goal_key not in goal_options:
            return Response(
                'Provided goal key, {goal_key}, is not a valid goal key (options= {goal_options}).'.format(
                    goal_key=goal_key,
                    goal_options=goal_options,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure course key is valid
        course_key = CourseKey.from_string(post_data.data['course_key'])
        if not course_key:
            return Response(
                'Provided course_key ({course_key}) does not map to a course.'.format(
                    course_key=course_key
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = post_data.user
        goal = CourseGoal.objects.filter(user=user.id, course_key=course_key).first()
        if goal:
            goal.goal_key = goal_key
            goal.save(update_fields=['goal_key'])
        else:
            CourseGoal.objects.create(
                user=user,
                course_key=course_key,
                goal_key=goal_key,
            )
        data = {
            'goal_key': str(goal_key),
            'goal_text': str(goal_options[goal_key]),
            'is_unsure': goal_key == GOAL_KEY_CHOICES.unsure,
        }
        return JsonResponse(data, content_type="application/json", status=(200 if goal else 201))  # lint-amnesty, pylint: disable=redundant-content-type-for-json-response


class PopulateUserActivity(APIView):
    """
    API that allows external callers to populate the user activity table
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsStaffOrOwner,)

    def post(self, request):
        """
        Handle the POST request

        Populate the user activity table.
        """
        user_id = request.data.get('user_id')
        course_key = request.data.get('course_key')

        if not user_id or not course_key:
            return Response(
                'User id and course key are required',
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = int(user_id)
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                'Provided user id does not correspond to an existing user',
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            course_key = CourseKey.from_string(course_key)
        except InvalidKeyError:
            return Response(
                'Provided course key is not valid',
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Populate user activity for tracking progress towards a user's course goals
        (activity_object_id, created) = UserActivity.populate_user_activity(user, course_key)
        if activity_object_id:
            data = {
                'activity_object_id': activity_object_id
            }
            return JsonResponse(data, status=(201 if created else 200))
        else:
            return Response(
                'User Activity was not populated',
                status=status.HTTP_400_BAD_REQUEST,
            )
