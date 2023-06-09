from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from common.djangoapps.edxmako.shortcuts import render_to_response

@login_required
@ensure_csrf_cookie
def instructor_tools_dashboard(request):
    response = render_to_response('instructor_tools/instructor_tools_dashboard.html', {})

    return response