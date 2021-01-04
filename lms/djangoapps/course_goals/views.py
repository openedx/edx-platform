"""
Course Goals Views - includes REST API
"""


from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import JsonResponse
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from eventtracking import tracker
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from openedx.core.lib.api.permissions import IsStaffOrOwner
from common.djangoapps.track import segment

from .api import get_course_goal_options
from .models import GOAL_KEY_CHOICES, CourseGoal

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

    # Another version of this endpoint exists in ../course_home_api/outline/v1/views.py
    def create(self, post_data):
        """ Create a new goal if one does not exist, otherwise update the existing goal. """
        # Ensure goal_key is valid
        goal_options = get_course_goal_options()
        goal_key = post_data.data.get('goal_key')
        if not goal_key:
            return Response(
                u'Please provide a valid goal key from following options. (options= {goal_options}).'.format(
                    goal_options=goal_options,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif goal_key not in goal_options:
            return Response(
                u'Provided goal key, {goal_key}, is not a valid goal key (options= {goal_options}).'.format(
                    goal_key=goal_key,
                    goal_options=goal_options,
                ),
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure course key is valid
        course_key = CourseKey.from_string(post_data.data['course_key'])
        if not course_key:
            return Response(
                u'Provided course_key ({course_key}) does not map to a course.'.format(
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
        return JsonResponse(data, content_type="application/json", status=(200 if goal else 201))


@receiver(post_save, sender=CourseGoal, dispatch_uid="emit_course_goals_event")
def emit_course_goal_event(sender, instance, **kwargs):
    """Emit events for both tracking logs and for Segment."""
    name = 'edx.course.goal.added' if kwargs.get('created', False) else 'edx.course.goal.updated'
    tracker.emit(
        name,
        {
            'goal_key': instance.goal_key,
        }
    )
    segment.track(instance.user.id, name)
