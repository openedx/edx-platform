import re
from urlparse import urlparse

from django.http import Http404
from django.shortcuts import redirect

from courseware.courses import check_course


class Middleware(object):
    """
    This middleware is to keep the course nav bar above the wiki while
    the student clicks around to other wiki pages.
    If it intercepts a request for /wiki/.. that has a referrer in the
    form /courses/course_id/... it will redirect the user to the page
    /courses/course_id/wiki/...
    """
    
    def process_request(self, request):
        #TODO: We should also redirect people who can't see the class to the regular wiki, so urls don't break
        
        referer = request.META.get('HTTP_REFERER')
        
        try:
            parsed_referer = urlparse(referer)
            referer_path = parsed_referer.path
        except:
            referer_path =""
        
        path_match = re.match(r'^/wiki/(?P<wiki_path>.*|)$', request.path)
        if path_match:
            # We are going to the wiki. Check if we came from a course
            course_match = re.match(r'/courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/.*', referer_path)
            if course_match:
                course_id = course_match.group('course_id')
                
                # See if we are able to view the course. If we are, redirect to it
                try:
                    course = check_course(request.user, course_id)
                    return redirect("/courses/" + course.id + "/view_wiki/" + path_match.group('wiki_path') )
                    
                except Http404:
                    # Even though we came from the course, we can't see it. So don't worry about it.
                    pass
                
        return None

def context_processor(request):
    """
    This is a context processor which looks at the URL while we are
    in the wiki. If the url is in the form
    /courses/(course_id)/wiki/...
    then we add 'course' to the context. This allows the course nav
    bar to be shown.
    """
    
    match = re.match(r'^/courses/(?P<course_id>[^/]+/[^/]+/[^/]+)/view_wiki(?P<wiki_path>.*|)', request.path)
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
    