from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.views.decorators.http import require_GET
from util.json_request import JsonResponse

from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment

from .helpers import populate_trophycase, get_course_badges
from .models import UserBadge


@require_GET
@login_required
def trophycase(request):
    user = request.user

    # Get course id and course name of courses user is enrolled in
    enrolled_courses_data = CourseEnrollment.enrollments_for_user(user).order_by(
        'course__display_name').values_list('course_id', 'course__display_name')

    # list of badges earned by user
    earned_user_badges = list(
        UserBadge.objects.filter(user=user)
    )

    trophycase_dict = populate_trophycase(user, enrolled_courses_data, earned_user_badges)

    return render_to_response(
            "features/badging/trophy_case.html",
            {
                'trophycase_data': trophycase_dict
            }
        )


@require_GET
@login_required
def my_badges(request, course_id):
    user = request.user

    course_key = CourseKey.from_string(unicode(course_id))
    if not CourseEnrollment.is_enrolled(user, course_key):
        raise Http404

    # list of badges earned by user
    earned_user_badges = list(
        UserBadge.objects.filter(user=user, course_id=course_key)
    )

    badges = get_course_badges(user, course_key, earned_user_badges)

    return JsonResponse(badges)
