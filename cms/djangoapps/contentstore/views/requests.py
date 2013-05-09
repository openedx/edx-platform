from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie
from mitxmako.shortcuts import render_to_response
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from access import has_access
from contentstore.utils import get_url_reverse, get_lms_link_for_item
from django.conf import settings

@login_required
@ensure_csrf_cookie
def index(request):
    """
    List all courses available to the logged in user
    """
    courses = modulestore('direct').get_items(['i4x', None, None, 'course', None])

    # filter out courses that we don't have access too
    def course_filter(course):
        return (has_access(request.user, course.location)
                and course.location.course != 'templates'
                and course.location.org != ''
                and course.location.course != ''
                and course.location.name != '')
    courses = filter(course_filter, courses)

    return render_to_response('index.html', {
        'new_course_template': Location('i4x', 'edx', 'templates', 'course', 'Empty'),
        'courses': [(course.display_name,
                    get_url_reverse('CourseOutline', course),
                    get_lms_link_for_item(course.location, course_id=course.location.course_id))
                    for course in courses],
        'user': request.user,
        'disable_course_creation': settings.MITX_FEATURES.get('DISABLE_COURSE_CREATION', False) and not request.user.is_staff
    })


# ==== Views with per-item permissions================================


# points to the temporary course landing page with log in and sign up
def landing(request, org, course, coursename):
    return render_to_response('temp-course-landing.html', {})

# points to the temporary edge page
def edge(request):
    return render_to_response('university_profiles/edge.html', {})


def event(request):
    '''
    A noop to swallow the analytics call so that cms methods don't spook and poor developers looking at
    console logs don't get distracted :-)
    '''
    return HttpResponse(True)


def get_request_method(request):
    """
    Using HTTP_X_HTTP_METHOD_OVERRIDE, in the request metadata, determine
    what type of request came from the client, and return it.
    """
    # NB: we're setting Backbone.emulateHTTP to true on the client so everything comes as a post!!!
    if request.method == 'POST' and 'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META:
        real_method = request.META['HTTP_X_HTTP_METHOD_OVERRIDE']
    else:
        real_method = request.method

    return real_method

def create_json_response(errmsg=None):
    if errmsg is not None:
        resp = HttpResponse(json.dumps({'Status': 'Failed', 'ErrMsg': errmsg}))
    else:
        resp = HttpResponse(json.dumps({'Status': 'OK'}))

    return resp

def render_from_lms(template_name, dictionary, context=None, namespace='main'):
    """
    Render a template using the LMS MAKO_TEMPLATES
    """
    return render_to_string(template_name, dictionary, context, namespace="lms." + namespace)


def _xmodule_recurse(item, action):
    for child in item.get_children():
        _xmodule_recurse(child, action)

    action(item)

