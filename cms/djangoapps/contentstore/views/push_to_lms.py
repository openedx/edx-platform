import os
import logging

from django.conf import settings
from django_future.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required

from mitxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore

from .access import get_location_and_verify_access

log = logging.getLogger(__name__)

@ensure_csrf_cookie
@login_required
def push_to_lms(request, org, course, name):
    """
    This method serves up the 'Push to LMS' page
    """
    location = get_location_and_verify_access(request, org, course, name)

    course_module = modulestore().get_item(location)

    log.debug('push_to_lms course_module=%s' % course_module)

    msg = ""

    if 'action' in request.GET and course_module.lms.giturl:
        # do the push, using script
        doexport = getattr(settings, 'CMS_EXPORT_COURSE_SCRIPT', '')
        if doexport and os.path.exists(doexport):
            cmd = '{0} {1} {2} {3}'.format(doexport, course_module.id, request.user, course_module.lms.giturl)
            msg = os.popen(cmd).read()

    return render_to_response('push_to_lms.html', {
        'context_course': course_module,
        'msg': msg,
    })
