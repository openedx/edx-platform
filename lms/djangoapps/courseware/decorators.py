from django.http import Http404

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore

def check_course(course_must_be_open=True, course_required=True):
    """
    This is a decorator for views that are within a course.
    It converts the string passed to the view as 'course_id'
    to a course, and then passes it to the view function as
    a parameter named 'course'.
    
    This decorator also checks that the course has started.
    If the course has not started, it raises a 404. This check
    can be skipped by setting course_must_be_open to False.
    
    If course_required is False, course_id is not required. If
    course_id is still provided, but is None, course will be
    set to None.
    """
    def inner_check_course(function):
        def wrapped_function(*args, **kwargs):
            if course_required or 'course_id' in kwargs:
                course_id = kwargs['course_id']
                course = None
                
                if course_required or course_id:
                    try:
                        course_loc = CourseDescriptor.id_to_location(course_id)
                        course = modulestore().get_item(course_loc)
                    except KeyError:
                        raise Http404("Course not found.")
                    
                    if course_must_be_open and not course.has_started():
                        raise Http404("This course has not yet started.")
        
                del kwargs['course_id']
                kwargs['course'] = course
        
            return function(*args, **kwargs)
        return wrapped_function
        
    # If no arguments were passed to the decorator, the function itself
    # will be in course_must_be_open
    if hasattr(course_must_be_open, '__call__'):
        function = course_must_be_open
        course_must_be_open = True
        return inner_check_course(function)
    else:
        return inner_check_course
