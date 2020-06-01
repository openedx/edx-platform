from courseware.courses import get_courses
from custom_settings.models import CustomSettings

from xmodule.modulestore.django import modulestore


def get_featured_courses(user):
    featured_courses = []

    courses = get_courses(user)
    featured_custom_settings = CustomSettings.objects.filter(is_featured=True).values_list('id', flat=True)
    for course in courses:
        if course.id in featured_custom_settings:
            course_details = modulestore().get_course(course.id)
            instructors = course_details.instructor_info.get('instructors')
            course.instructors = instructors if instructors else []
            featured_courses += [course]

    return featured_courses
