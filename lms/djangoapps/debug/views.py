"""Views for debugging and diagnostics"""

import pprint

from django.http import Http404
from django.contrib.auth.decorators import login_required
from django_future.csrf import ensure_csrf_cookie, csrf_exempt
from mitxmako.shortcuts import render_to_response

from codejail.safe_exec import safe_exec

@login_required
@ensure_csrf_cookie
def run_python(request):
    if not request.user.is_staff:
        raise Http404
    c = {}
    c['code'] = ''
    c['results'] = None
    if request.method == 'POST':
        py_code = c['code'] = request.POST.get('code')
        g, l = {}, {}
        try:
            safe_exec(py_code, g, l)
        except Exception as e:
            c['results'] = str(e)
        else:
            c['results'] = pprint.pformat(l)
    return render_to_response("debug/run_python_form.html", c)
