"""
Course API
"""

from django.contrib.auth.models import User
from django.template import defaultfilters
from rest_framework import status
from rest_framework.response import Response

from opaque_keys.edx.keys import CourseKey

from xmodule.course_module import DEFAULT_START_DATE

from courseware.courses import (
    get_courses,
    course_image_url,
    get_course_about_section,
)


def has_permission(request, username):

    if not username:
        return False

    user = request.user
    return user and (user.is_staff or user.username == username)


def course_view(request, course_key_string):

    course_key = CourseKey.from_string(course_key_string)
    course_usage_key = modulestore().make_course_usage_key(course_key)

    return Response({
        'blocks_url': reverse(
                    'blocks_in_block_tree',
                    kwargs={'usage_key_string': unicode(course_usage_key)},
                    request=request,
                    )
    })


def list_courses(request, username):

    if (has_permission(request, username) is not True):
        return Response('Unauthorized', status=status.HTTP_403_FORBIDDEN)

    if (username != ''):
        new_user = User.objects.get(username=username)
    else:
        new_user = request.user

    courses = get_courses(new_user)
    courses_json = []

    for course in courses:
        if course.advertised_start is not None:
            start_type = "string"
            start_display = course.advertised_start
        elif course.start != DEFAULT_START_DATE:
            start_type = "timestamp"
            start_display = defaultfilters.date(course.start, "DATE_FORMAT")
        else:
            start_type = "empty"
            start_display = None

        courses_json.append({
            "id": unicode(course.id),
            "name": course.display_name_with_default,
            "number": course.display_number_with_default,
            "org": course.display_org_with_default,
            "description": get_course_about_section(course, "short_description").strip(),
            "start": course.start,
            "start_display": start_display,
            "start_type": start_type,
            "end": course.end,
            "enrollment_start": course.enrollment_start,
            "enrollment_end": course.enrollment_end,
            "course_image": course_image_url(course),
        })

    return Response(courses_json)
