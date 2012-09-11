# View for semi-static templatized content.
#
# List of valid templates is explicitly managed for (short-term)
# security reasons.

from mitxmako.shortcuts import render_to_response, render_to_string
from django.shortcuts import redirect
from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseServerError
from django_future.csrf import ensure_csrf_cookie

from util.cache import cache_if_anonymous

valid_templates = []

if settings.STATIC_GRAB:
    valid_templates = valid_templates + ['server-down.html',
                                       'server-error.html'
                                       'server-overloaded.html',
                                       ]


def index(request, template):
    if template in valid_templates:
        return render_to_response('static_templates/' + template, {})
    else:
        return redirect('/')


@ensure_csrf_cookie
@cache_if_anonymous
def render(request, template):
    """
    This view function renders the template sent without checking that it
    exists. Do not expose template as a regex part of the url. The user should
    not be able to ender any arbitray template name. The correct usage would be:

    url(r'^jobs$', 'static_template_view.views.render', {'template': 'jobs.html'}, name="jobs")
    """
    return render_to_response('static_templates/' + template, {})


def render_404(request):
    return HttpResponseNotFound(render_to_string('static_templates/404.html', {}))


def render_500(request):
    return HttpResponseServerError(render_to_string('static_templates/server-error.html', {}))

