from django.contrib.auth.models import AnonymousUser

from common.lib.nodebb_client.client import NodeBBClient
from courseware.courses import get_courses
from custom_settings.models import CustomSettings
from edxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore


def home_page(request, user=AnonymousUser()):
    """
    Override the default homepage for students
    """
    featured_courses = get_featured_courses(user)
    status_code, featured_categories = NodeBBClient().categories.featured()

    context = {
        'courses': featured_courses,
        'categories': featured_categories if status_code == 200 else [],
    }

    return render_to_response("homepage/homepage.html", context)


def get_featured_courses(user):
    featured_courses = []

    courses = get_courses(user)
    featured_custom_settings = CustomSettings.objects.filter(is_featured=True).values_list('id', flat=True)
    for course in courses:
        if unicode(course.id) in featured_custom_settings:
            course_details = modulestore().get_course(course.id)
            instructors = course_details.instructor_info.get('instructors')
            course.instructors = instructors if instructors else []
            featured_courses += [course]

    return featured_courses
