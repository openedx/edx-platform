from functools import wraps

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
    
    Usually, a 404 will be raised if a course is not found. This
    behavior can be overrided by setting course_required to false.
    When course_required is False, course_id is not required. If
    course_id is still provided, but is None, course will be
    set to None.
    
    Usage
    This wrapper would be used on a function that has the following
    entry in urls.py:
    
    url(r'^courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/book$', 'staticbook.views.index'),
     
    Where staticbook.views.index has the following parameters:
    
    @check_course
    def index(request, course):
        # Notice that the parameter is course, not course_id
    """
    def inner_check_course(function):
        @wraps(function)
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
    if callable(course_must_be_open):
        function = course_must_be_open
        course_must_be_open = True
        return inner_check_course(function)
    else:
        return inner_check_course
