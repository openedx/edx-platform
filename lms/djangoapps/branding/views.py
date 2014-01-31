from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect
from django_future.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response

import student.views
import courseware.views

from microsite_configuration.middleware import MicrositeConfiguration
from edxmako.shortcuts import marketing_link
from util.cache import cache_if_anonymous

from courseware.courses import get_courses
from django.utils.translation import ugettext_lazy as _

@ensure_csrf_cookie
@cache_if_anonymous
def index(request):
    '''
    Redirects to main page -- info page if user authenticated, or marketing if not
    '''

    if settings.COURSEWARE_ENABLED and request.user.is_authenticated():
        return redirect(reverse('dashboard'))

    if settings.FEATURES.get('AUTH_USE_MIT_CERTIFICATES'):
        from external_auth.views import ssl_login
        return ssl_login(request)

    enable_mktg_site = MicrositeConfiguration.get_microsite_configuration_value(
        'ENABLE_MKTG_SITE',
        settings.FEATURES.get('ENABLE_MKTG_SITE', False)
    )

    if enable_mktg_site:
        return redirect(settings.MKTG_URLS.get('ROOT'))

    university = MicrositeConfiguration.match_university(request.META.get('HTTP_HOST'))

    # keep specialized logic for Edge until we can migrate over Edge to fully use
    # microsite definitions
    if university == 'edge':
        context = {
            'suppress_toplevel_navigation': True
        }
        return render_to_response('university_profile/edge.html', context)

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
    enable_mktg_site = settings.FEATURES.get('ENABLE_MKTG_SITE') or MicrositeConfiguration.get_microsite_configuration_value('ENABLE_MKTG_SITE', False)

    if enable_mktg_site:
        return redirect(marketing_link('COURSES'), permanent=True)

    if not settings.FEATURES.get('COURSES_ARE_BROWSABLE'):
        raise Http404

    #  we do not expect this case to be reached in cases where
    #  marketing is enabled or the courses are not browsable
    return courseware.views.courses(request)


SUBJECTS = (
        ('english', _('English Language')),
        ('astronomy', _('Astronomy')),
        ('biology', _('Biology')),
        ('geography', _('Geography')),
        ('natural_science', _('Natural Science')),
        ('computer_science', _('Computer Science')),
        ('history', _('History')),
        ('litrature', _('Literature')),
        ('mathematics', _('Mathematics')),
        ('world_art', _('World Art')),
        ('german', _('German Language')),
        ('obg', _('OBG')),
        ('social_studies', _('Social Studies')),
        ('law', _('Law')),
        ('psychology', _('Psychology')),
        ('russian', _('Russian Language')),
        ('technology', _('Technology')),
        ('physics', _('Physics')),
        ('physical_culture', _('Physical Culture')),
        ('french', _('French Language')),
        ('chemistry', _('Chemistry')),
        ('ecology', _('Ecology')),
        ('economy', _('Economy')),
    )


DESTINY = (
        ("advanced_training", _("Advanced training courses")),
        ("trainging_olymp", _("Training for the Olympics")),
        ("extra_education", _("Extra children's education")),
        ("supplementary", _("Supplementary courses")),
    )

@ensure_csrf_cookie
@cache_if_anonymous
def courses_list(request, status = "all", subject="all", destiny="all"):
    all_courses =  get_courses(request.user)
    courses = []
    for course in all_courses:
        if (status == "new"):
            if (not course.is_newish): continue
        elif (status ==  "past"):
            if (not course.has_ended()): continue
        elif (status == "current"):
            if (not course.has_started()): continue
        elif (status != "all"):
            continue
        if (subject != "all"):
            if not (subject in course.tags or dict(SUBJECTS).get(subject, '') in course.tags): continue
        if (destiny != "all"):
            if not (destiny in course.tags or dict(DESTINY).get(destiny, '') in course.tags): continue
        courses += [course]
    context = {'courses': courses, 'destiny': destiny, 'subject': subject}
    return render_to_response("courses_list.html", context)
