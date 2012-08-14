import re

from django.http import Http404
from django.shortcuts import redirect

from courseware.courses import check_course


def context_processor(request):
    """
    This is a context processor which looks at the URL while we are
    in the wiki. If the url is in the form
    /courses/(course_id)/wiki/...
    then we add 'course' to the context. This allows the course nav
    bar to be shown.
    """
    
    match = re.match(r'^/courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/wiki(?P<wiki_path>.*|)', request.path)
    if match:
        course_id = match.group('course_id')
        
        try:
            course = check_course(request.user, course_id)
            return {'course' : course}
        except Http404:
            # We couldn't access the course for whatever reason. It is too late to change
            # the URL here, so we just leave the course context. The middleware shouldn't
            # let this happen
            pass
            
    return {}
    