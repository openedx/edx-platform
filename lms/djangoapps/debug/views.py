"""Views for debugging and diagnostics"""

import pprint
import traceback

from django.http import Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.html import escape

from django.views.decorators.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response

from codejail.safe_exec import safe_exec


@login_required
@ensure_csrf_cookie
def run_python(request):
    """A page to allow testing the Python sandbox on a production server."""
    if not request.user.is_staff:
        raise Http404
    c = {}
    c['code'] = ''
    c['results'] = None
    if request.method == 'POST':
        py_code = c['code'] = request.POST.get('code')
        g = {}
        try:
            safe_exec(py_code, g)
        except Exception as e:
            c['results'] = traceback.format_exc()
        else:
            c['results'] = pprint.pformat(g)
    return render_to_response("debug/run_python_form.html", c)


@login_required
def show_parameters(request):
    """A page that shows what parameters were on the URL and post."""
    html = []
    for name, value in sorted(request.GET.items()):
        html.append(escape("GET {}: {!r}".format(name, value)))
    for name, value in sorted(request.POST.items()):
        html.append(escape("POST {}: {!r}".format(name, value)))
    return HttpResponse("\n".join("<p>{}</p>".format(h) for h in html))
