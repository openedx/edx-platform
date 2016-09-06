# View for semi-static templatized content.
#
# List of valid templates is explicitly managed for (short-term)
# security reasons.

import mimetypes

from edxmako.shortcuts import render_to_response, render_to_string
from mako.exceptions import TopLevelLookupException
from django.shortcuts import redirect
from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseServerError, Http404
from django.views.decorators.csrf import ensure_csrf_cookie

from util.cache import cache_if_anonymous

valid_templates = []

if settings.STATIC_GRAB:
    valid_templates = valid_templates + [
        'server-down.html',
        'server-error.html'
        'server-overloaded.html',
    ]


def index(request, template):
    if template in valid_templates:
        return render_to_response('static_templates/' + template, {})
    else:
        return redirect('/')


@ensure_csrf_cookie
@cache_if_anonymous()
def render(request, template):
    """
    This view function renders the template sent without checking that it
    exists. Do not expose template as a regex part of the url. The user should
    not be able to ender any arbitray template name. The correct usage would be:

    url(r'^jobs$', 'static_template_view.views.render', {'template': 'jobs.html'}, name="jobs")
    """

    # Guess content type from file extension
    content_type, __ = mimetypes.guess_type(template)

    try:
        return render_to_response('static_templates/' + template, {}, content_type=content_type)
    except TopLevelLookupException:
        raise Http404


@ensure_csrf_cookie
@cache_if_anonymous()
def render_press_release(request, slug):
    """
    Render a press release given a slug.  Similar to the "render" function above,
    but takes a slug and does a basic conversion to convert it to a template file.
    a) all lower case,
    b) convert dashes to underscores, and
    c) appending ".html"
    """
    template = slug.lower().replace('-', '_') + ".html"
    try:
        resp = render_to_response('static_templates/press_releases/' + template, {})
    except TopLevelLookupException:
        raise Http404
    else:
        return resp


def render_404(request):
    return HttpResponseNotFound(render_to_string('static_templates/404.html', {}, request=request))


def render_500(request):
    return HttpResponseServerError(render_to_string('static_templates/server-error.html', {}, request=request))
