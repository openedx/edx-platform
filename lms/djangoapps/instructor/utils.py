
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module, get_module_for_descriptor
from courseware.courses import get_course_by_id
from django.contrib.auth.models import User


def get_descriptor(course, location):
    if isinstance(course, str):
        course = get_course_by_id(course)
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

def create_module(descriptor, course, student, request):
    field_data_cache = FieldDataCache([descriptor], course.id, student)
    return get_module_for_descriptor(student, request, descriptor, field_data_cache, course.id)

def get_module_for_student(student_name, course_id, location):
    try:
        student = User.objects.get(username=student_name)
        request = DummyRequest()
        request.user = student
        request.session = {}
        course = get_course_by_id(course_id)
        descriptor = get_descriptor(course, location)
        module = create_module(descriptor, course, student, request)
        return module
    except Exception as e:
        print e.message
        return None


class DummyRequest(object):
    META = {}
    def __init__(self):
        return
    def get_host(self):
        return 'edx.mit.edu'
    def is_secure(self):
        return False