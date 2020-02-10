from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.views.decorators.http import require_GET

from courseware.courses import get_course_with_access
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
    """ this function returns badges related to on course """
    user = request.user

    course_key = CourseKey.from_string(unicode(course_id))
    course = get_course_with_access(user, 'load', course_key)
    if not CourseEnrollment.is_enrolled(user, course_key):
        raise Http404

    # list of badges earned by user
    earned_user_badges = list(
        UserBadge.objects.filter(user=user, course_id=course_key)
    )

    badges = get_course_badges(user, course_key, earned_user_badges)

    return render_to_response(
        'features/badging/my_badges.html',
        {
            'course': course,
            'badges': badges
        }
    )
