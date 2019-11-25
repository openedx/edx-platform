from django.views.decorators.http import require_GET
from util.json_request import JsonResponse

from student.models import CourseEnrollment

from .helpers import populate_trophycase
from .models import UserBadge


@require_GET
def trophycase(request):
    # Get course id and course name of courses user is enrolled in
    enrolled_courses_data = CourseEnrollment.enrollments_for_user(request.user).order_by(
        'course__display_name').values_list('course_id', 'course__display_name')

    # list of badges earned by user
    earned_user_badges = list(
        UserBadge.objects.filter(user=request.user)
    )

    trophycase_dict = populate_trophycase(enrolled_courses_data, earned_user_badges)

    return JsonResponse(trophycase_dict)
