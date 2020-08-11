from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from lms.djangoapps.courseware.courses import get_course_by_id


def can_view_teams(function):
    def wrap(request, *args, **kwargs):

        course_id = SlashSeparatedCourseKey.from_deprecated_string(kwargs['course_id'])
        course = get_course_by_id(course_id)

        if course.has_ended():
            redirect_url = reverse('teams_dashboard', args=[course.id])
            return redirect(redirect_url)

        return function(request, *args, **kwargs)

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap
