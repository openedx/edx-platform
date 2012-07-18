from functools import wraps

from django.conf import settings
from django.http import Http404

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore


def check_course(course_id, course_must_be_open=True, course_required=True):
    """
    Given a course_id, this returns the course object. By default,
    if the course is not found or the course is not open yet, this
    method will raise a 404.
    
    If course_must_be_open is False, the course will be returned
    without a 404 even if it is not open.
    
    If course_required is False, a course_id of None is acceptable. The
    course returned will be None. Even if the course is not required,
    if a course_id is given that does not exist a 404 will be raised.
    """
    course = None
    if course_required or course_id:
        try:
            course_loc = CourseDescriptor.id_to_location(course_id)
            course = modulestore().get_item(course_loc)
        except KeyError:
            raise Http404("Course not found.")
        
        if course_must_be_open and not course.has_started():
            raise Http404("This course has not yet started.")
    
    return course

def course_static_file_url(course, filepath):
    """
    Given a course and a filepath from the course's directory 
    (like images/course_image.png), this returns the url for 
    the static file in the form. It will be something like
    /static/content-mit-6002x/images/course_image.png.
    """
    return "/".join( [settings.STATIC_URL, course.metadata['data_dir'], filepath] )
    
def course_image_url(course):
    return course_static_file_url(course, "images/course_image.png")
    
    
    
    