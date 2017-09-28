"""
Course Goals Views - includes REST API
"""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from edx_rest_framework_extensions.authentication import JwtAuthentication
from eventtracking import tracker
from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api.permissions import IsStaffOrOwner
from rest_framework import permissions, serializers, viewsets
from rest_framework.authentication import SessionAuthentication

from .models import CourseGoal


User = get_user_model()


class CourseGoalSerializer(serializers.ModelSerializer):
    """
    Serializes CourseGoal models.
    """
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = CourseGoal
        fields = ('user', 'course_key', 'goal_key')

    def validate_course_key(self, value):
        """
        Ensure that the course_key is valid.
        """
        course_key = CourseKey.from_string(value)
        if not course_key:
            raise serializers.ValidationError(
                'Provided course_key ({course_key}) does not map to a course.'.format(
                    course_key=course_key
                )
            )
        return course_key


class CourseGoalViewSet(viewsets.ModelViewSet):
    """
    API calls to create and retrieve a course goal.

    **Use Case**
        * Create a new goal for a user.

            Http400 is returned if the format of the request is not correct,
            the course_id or goal is invalid or cannot be found.

        * Retrieve goal for a user and a particular course.

            Http400 is returned if the format of the request is not correct,
            or the course_id is invalid or cannot be found.

    **Example Requests**
        GET /api/course_goals/v0/course_goals/
        POST /api/course_goals/v0/course_goals/
            Request data: {"course_key": <course-key>, "goal_key": "<goal-key>", "user": "<username>"}

    """
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsStaffOrOwner,)
    queryset = CourseGoal.objects.all()
    serializer_class = CourseGoalSerializer


@receiver(post_save, sender=CourseGoal, dispatch_uid="emit_course_goals_event")
def emit_course_goal_event(sender, instance, **kwargs):
    name = 'edx.course.goal.added' if kwargs.get('created', False) else 'edx.course.goal.updated'
    tracker.emit(
        name,
        {
            'goal_key': instance.goal_key,
        }
    )
