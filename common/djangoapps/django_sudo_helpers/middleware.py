"""
Django sudo middleware.
"""
from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey


class DjangoSudoMiddleware(object):
    """
    Django sudo middleware to load course/library.
    """

    def process_request(self, request):
        """ Process the middleware request. """
        if 'region' in request.GET:
            load_course_or_library(request)


def load_course_or_library(request):
    """
    Get course/library from region if not None and set on request object.
    """
    region = request.GET.get('region')
    if region:
        # parse out the course_id into a course_key
        try:
            course_key = CourseKey.from_string(region)
            if 'library' in region:
                request.library = modulestore().get_library(course_key)
            else:
                request.course = modulestore().get_course(course_key)
        except InvalidKeyError:
            pass
