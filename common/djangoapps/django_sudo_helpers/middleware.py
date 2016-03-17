"""
Django sudo middleware.
"""

from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from .utils import emit_sudo_event


class DjangoSudoMiddleware(object):
    """
    Django sudo middleware to load course/library.
    """

    def process_request(self, request):
        """ Process the middleware request. """
        if 'region' in request.GET:
            load_course_or_library(request)

    def process_response(self, request, response):
        """Process the middleware response."""
        if request.path.startswith('/sudo/') and request.method == 'POST':
            emit_sudo_event(
                request, request.user, request.GET.get('region'), request.GET.get('next')
            )

        return response


def load_course_or_library(request):
    """
    Get course/library from region if not None and set on request object.
    """
    region = request.GET.get('region')
    if region:
        # parse out the course_id into a course_key
        try:
            course_key = CourseKey.from_string(region)
            if 'library-' in region:
                request.library = modulestore().get_library(course_key)
            else:
                request.course = modulestore().get_course(course_key)
        except InvalidKeyError:
            pass
