from django.conf import settings
from django.core.urlresolvers import reverse
from branding.models import BrandingApiConfig
from django.http import Http404
from django.shortcuts import redirect
from django_future.csrf import ensure_csrf_cookie

import student.views
from student.models import CourseEnrollment

import courseware.views

from microsite_configuration import microsite
from edxmako.shortcuts import marketing_link
from util.cache import cache_if_anonymous
from .api import get_footer_json, get_footer_static, get_footer_html
from util.json_request import JsonResponse, HttpResponse


def get_course_enrollments(user):
    """
    Returns the course enrollments for the passed in user within the context of a microsite, that
    is filtered by course_org_filter
    """
    enrollments = CourseEnrollment.enrollments_for_user(user)
    microsite_org = microsite.get_value('course_org_filter')
    if microsite_org:
        site_enrollments = [
            enrollment for enrollment in enrollments if enrollment.course_id.org == microsite_org
        ]
    else:
        site_enrollments = [
            enrollment for enrollment in enrollments
        ]
    return site_enrollments


@ensure_csrf_cookie
@cache_if_anonymous()
def index(request):
    '''
    Redirects to main page -- info page if user authenticated, or marketing if not
    '''

    if settings.COURSEWARE_ENABLED and request.user.is_authenticated():
        # For microsites, only redirect to dashboard if user has
        # courses in his/her dashboard. Otherwise UX is a bit cryptic.
        # In this case, we want to have the user stay on a course catalog
        # page to make it easier to browse for courses (and register)
        if microsite.get_value(
            'ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER',
            settings.FEATURES.get('ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER', True)
        ):
            return redirect(reverse('dashboard'))

    if settings.FEATURES.get('AUTH_USE_CERTIFICATES'):
        from external_auth.views import ssl_login
        # Set next URL to dashboard if it isn't set to avoid
        # caching a redirect to / that causes a redirect loop on logout
        if not request.GET.get('next'):
            req_new = request.GET.copy()
            req_new['next'] = reverse('dashboard')
            request.GET = req_new
        return ssl_login(request)

    enable_mktg_site = microsite.get_value(
        'ENABLE_MKTG_SITE',
        settings.FEATURES.get('ENABLE_MKTG_SITE', False)
    )

    if enable_mktg_site:
        return redirect(settings.MKTG_URLS.get('ROOT'))

    domain = request.META.get('HTTP_HOST')

    # keep specialized logic for Edge until we can migrate over Edge to fully use
    # microsite definitions
    if domain and 'edge.edx.org' in domain:
        return redirect(reverse("signin_user"))

    #  we do not expect this case to be reached in cases where
    #  marketing and edge are enabled
    return student.views.index(request, user=request.user)


@ensure_csrf_cookie
@cache_if_anonymous()
def courses(request):
    """
    Render the "find courses" page. If the marketing site is enabled, redirect
    to that. Otherwise, if subdomain branding is on, this is the university
    profile page. Otherwise, it's the edX courseware.views.courses page
    """
    enable_mktg_site = microsite.get_value(
        'ENABLE_MKTG_SITE',
        settings.FEATURES.get('ENABLE_MKTG_SITE', False)
    )

    if enable_mktg_site:
        return redirect(marketing_link('COURSES'), permanent=True)

    if not settings.FEATURES.get('COURSES_ARE_BROWSABLE'):
        raise Http404

    #  we do not expect this case to be reached in cases where
    #  marketing is enabled or the courses are not browsable
    return courseware.views.courses(request)


def footer(request):
    # if configuration is not enabled then return 404
    if not BrandingApiConfig.current().enabled:
        raise Http404
    if "application/json" in request.META.get('HTTP_ACCEPT') or "*/*" in request.META.get('HTTP_ACCEPT'):
        return JsonResponse(get_footer_json(), 200)
    elif "text/html" in request.META.get('HTTP_ACCEPT'):
        html = get_footer_html()
        return HttpResponse(html, status=200)
    elif "text/javascript" in request.META.get('HTTP_ACCEPT'):
        try:
            content = get_footer_static("footer.js")
        except IOError:
            return HttpResponse(content="No js file found", status=404)
        return HttpResponse(content, content_type='text/javascript', status=200)
    elif "text/css" in request.META.get('HTTP_ACCEPT'):
        try:
            content = get_footer_static("footer.css")
        except IOError:
            return HttpResponse(content="No css file found", status=404)
        return HttpResponse(content, content_type='text/css', status=200)
    else:
        return HttpResponse(status=406)
