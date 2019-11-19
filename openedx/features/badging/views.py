from collections import OrderedDict
from django.views.decorators.http import require_GET
from student.models import CourseEnrollment
from util.json_request import JsonResponse

from .helpers import create_torphycase_data
from .models import Badge, UserBadge


@require_GET
def trophycase(request):
    # Get course id and course name of courses user is enrolled in
    enrolled_courses_data = CourseEnrollment.enrollments_for_user(request.user).order_by(
        'course__display_name').values_list('course_id', 'course__display_name')

    # list of badges earned by user
    earned_user_badges = list(
        UserBadge.objects.filter(user=request.user).values()
    )

    trophycase_dict = OrderedDict()

    # Get all badges by their types and add under each enrolled course
    for badge_type_tuple in Badge.BADGE_TYPES:
        badge_type, _ = badge_type_tuple
        # list of all badges of a specific type
        all_badges = list(
            Badge.objects.filter(type=badge_type).order_by('threshold').values()
        )
        create_torphycase_data(trophycase_dict, badge_type, all_badges, earned_user_badges, enrolled_courses_data)

    return JsonResponse(trophycase_dict)
