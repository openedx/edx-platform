"""
This views handles exporting the course xml to a git repository if
the giturl attribute is set.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.translation import ugettext as _

from student.auth import has_course_author_access
import contentstore.git_export_utils as git_export_utils
from edxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey

log = logging.getLogger(__name__)


@ensure_csrf_cookie
@login_required
def export_git(request, course_key_string):
    """
    This method serves up the 'Export to Git' page
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    course_module = modulestore().get_course(course_key)
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
                msg = unicode(ex)

    return render_to_response('export_git.html', {
        'context_course': course_module,
        'msg': msg,
        'failed': failed,
    })
