""" Course Goals API """
import api

from django.http import Http404, JsonResponse
from rest_framework import serializers, viewsets

from .models import CourseGoal


class CourseGoalSerializer(serializers.ModelSerializer):
    """
    Serializes CourseGoal models.
    """
    class Meta:
        model = CourseGoal
        fields = ('user', 'course_key', 'goal_key')


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
        GET /course_goal/api/v0/course_goal?course_key={course_key1}
        POST /course_goal/api/v0/course_goal?course_key={course_key1}&goal={goal}
            Request data: {"course_key": <course-key>, "goal_key": "unsure"}

    Returns an HttpResponse Object with a success message html stub.

    """
    queryset = CourseGoal.objects.all()
    serializer_class = CourseGoalSerializer

    def post(self, request, *args, **kwargs):
        """
        Attempt to create course goal.
        """
        if not request.data:
            raise Http404

        course_id = request.data.get('course_key')
        if not course_id:
            raise Http404('Must provide a course_id')

        goal_key = request.data.get('goal_key')
        if not goal_key:
            raise Http404('Must provide a goal_key')

        api.add_course_goal(request.user, course_id, goal_key)

        return JsonResponse({
            'success': True,
        })
