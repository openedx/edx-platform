
from xmodule.modulestore.django import modulestore

from .models import CourseOverviewDescriptor

def get_course_overview(course_id):
    course_overview = None
    try:
        course_overview = CourseOverviewDescriptor.objects.get(id=course_id)
        course_overview.kdbg_cache_hit = True
    except CourseOverviewDescriptor.DoesNotExist:
        course = modulestore().get_course(course_id)
        if course:
            course_overview = CourseOverviewDescriptor.create_from_course(course)
            course_overview.save()
            course_overview.kdbg_cache_hit = False
    return course_overview
