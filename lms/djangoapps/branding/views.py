from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect
from django_future.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response

import student.views
import branding
import courseware.views
from edxmako.shortcuts import marketing_link
from util.cache import cache_if_anonymous


@ensure_csrf_cookie
@cache_if_anonymous
def index(request):
    '''
    Redirects to main page -- info page if user authenticated, or marketing if not
    '''

    if settings.COURSEWARE_ENABLED and request.user.is_authenticated():
        return redirect(reverse('dashboard'))

    if settings.MITX_FEATURES.get('AUTH_USE_MIT_CERTIFICATES'):
        from external_auth.views import ssl_login
        return ssl_login(request)
    if settings.MITX_FEATURES.get('ENABLE_MKTG_SITE'):
        return redirect(settings.MKTG_URLS.get('ROOT'))

    university = branding.get_university(request.META.get('HTTP_HOST'))
    if university == 'edge':
        return render_to_response('university_profile/edge.html', {})

    #  we do not expect this case to be reached in cases where
    #  marketing and edge are enabled
    return student.views.index(request, user=request.user)



@ensure_csrf_cookie
@cache_if_anonymous
def courses(request):
    """
    Render the "find courses" page. If the marketing site is enabled, redirect
    to that. Otherwise, if subdomain branding is on, this is the university
    profile page. Otherwise, it's the edX courseware.views.courses page
    """
    if settings.MITX_FEATURES.get('ENABLE_MKTG_SITE', False):
        return redirect(marketing_link('COURSES'), permanent=True)

    if not settings.MITX_FEATURES.get('COURSES_ARE_BROWSABLE'):        
        raise Http404

    #  we do not expect this case to be reached in cases where
    #  marketing is enabled or the courses are not browsable
    return courseware.views.courses(request)
