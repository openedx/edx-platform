"""
This views handles exporting the course xml to a git repository if
the giturl attribute is set.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django_future.csrf import ensure_csrf_cookie
from django.utils.translation import ugettext as _

from .access import has_course_access
import contentstore.git_export_utils as git_export_utils
from edxmako.shortcuts import render_to_response
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


@ensure_csrf_cookie
@login_required
def export_git(request, org, course, name):
    """
    This method serves up the 'Export to Git' page
    """
    location = Location('i4x', org, course, 'course', name)
    if not has_course_access(request.user, location):
        raise PermissionDenied()
    course_module = modulestore().get_item(location)
    failed = False

    log.debug('export_git course_module=%s', course_module)

    msg = ""
    if 'action' in request.GET and course_module.giturl:
        if request.GET['action'] == 'push':
            try:
                git_export_utils.export_to_git(
                    course_module.id,
                    course_module.giturl,
                    request.user,
                )
                msg = _('Course successfully exported to git repository')
            except git_export_utils.GitExportError as ex:
                failed = True
                msg = str(ex)

    return render_to_response('export_git.html', {
        'context_course': course_module,
        'msg': msg,
        'failed': failed,
    })
