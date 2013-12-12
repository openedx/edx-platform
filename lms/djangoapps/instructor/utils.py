
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor
from courseware.courses import get_course_by_id
from django.contrib.auth.models import User


def get_descriptor(course_id, location):
    """Find descriptor for the location in the course."""

    course = get_course_by_id(course_id)
    grading_context = course.grading_context
    descriptor = None
    for section_format, sections in grading_context['graded_sections'].iteritems():
        try:
            for section in sections:
                section_descriptor = section['section_descriptor']
                descriptor = find_descriptor_in_children(section_descriptor, location)
                if descriptor:
                    break

            if descriptor:
                break

        except Exception as err:
            print err.message

    return descriptor


def find_descriptor_in_children(descriptor, location):
    """Recursively look for location in descriptors children."""

    try:
        if descriptor.id == location:
            return descriptor
        children = descriptor.get_children()
    except:
        children = []
    for module_descriptor in children:
        child_descriptor = find_descriptor_in_children(module_descriptor, location)
        if child_descriptor:
            return child_descriptor
    return None


def create_module(student, course, descriptor, request):
    """Create module for student from descriptor."""

    field_data_cache = FieldDataCache([descriptor], course.id, student)
    return get_module_for_descriptor(student, request, descriptor, field_data_cache, course.id)


def get_module_for_student(student, course, location, request=None):
    """Return module for student from location."""

    if isinstance(student, str):
        try:
            student = User.objects.get(username=student)
        except User.DoesNotExist:
            return None

    if request is None:
        request = DummyRequest()
        request.user = student
        request.session = {}
    if isinstance(course, str):
        course = get_course_by_id(course)
        if course is None:
            return None
    descriptor = get_descriptor(course.id, location)
    module = create_module(student, course, descriptor, request)
    return module


def get_enrolled_students(course_id):
    """Return enrolled students for course."""

    enrolled_students = User.objects.filter(
        courseenrollment__course_id=course_id,
        courseenrollment__is_active=1
    ).prefetch_related("groups").order_by('username')
    return enrolled_students


class DummyRequest(object):
    """Dummy request"""

    META = {}

    def __init__(self):
        return

    def get_host(self):
        return 'edx.mit.edu'

    def is_secure(self):
        return False
