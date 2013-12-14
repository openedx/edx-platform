"""
This views handles exporting the course xml to a git repository if
the giturl attribute is set.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django_future.csrf import ensure_csrf_cookie
from django.utils.translation import ugettext as _

from .access import has_access
from edxmako.shortcuts import render_to_response
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
import contentstore.management.commands.git_export as git_export

log = logging.getLogger(__name__)


@ensure_csrf_cookie
@login_required
def push_to_lms(request, org, course, name):
    """
    This method serves up the 'Push to LMS' page
    """
    location = Location('i4x', org, course, 'course', name)
    if not has_access(request.user, location):
        raise PermissionDenied()
    course_module = modulestore().get_item(location)
    failed = False

    log.debug('push_to_lms course_module=%s', course_module)

    msg = ""
    if 'action' in request.GET and course_module.giturl:
        if request.GET['action'] == 'push':
            try:
                git_export.export_to_git(
                    course_module.id,
                    course_module.giturl,
                    request.user,
                )
                msg = _('Course successfully exported to git repository')
            except git_export.GitExportError as ex:
                failed = True
                msg = str(ex)

    return render_to_response('push_to_lms.html', {
        'context_course': course_module,
        'msg': msg,
        'failed': failed,
    })
