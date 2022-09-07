"""
Temporary views as workarounds until we upgrade the platform
"""

from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from lms.djangoapps.courseware.views.views import jump_to

from openedx.features.course_experience.urls import COURSE_HOME_VIEW_NAME


@ensure_csrf_cookie
def resume_to(_request, course_id, location):
    """
    A workaround to fix a big that we couldn't cherry-pick its fixing-commit. See RED-3276

    We'll call the original `jump_to` view, then handle any Http404 exception and forward to course home page
    """
    try:
        return jump_to(_request, course_id, location)
    except Http404:
        return redirect(reverse(COURSE_HOME_VIEW_NAME, args=[course_id]))
