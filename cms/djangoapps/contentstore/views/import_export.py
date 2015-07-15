"""
These views handle all actions in Studio related to import and exporting of
courses
"""
import logging
from opaque_keys import InvalidKeyError
import re

from contentstore.utils import reverse_course_url, reverse_library_url, reverse_usage_url

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods

from django.views.decorators.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator

from student.auth import has_course_author_access
from util.views import ensure_valid_course_key
from xmodule.modulestore.django import modulestore

from urllib import urlencode


__all__ = ["import_handler", "export_handler"]


log = logging.getLogger(__name__)


# Regex to capture Content-Range header ranges.
CONTENT_RE = re.compile(
    r"(?P<start>\d{1,11})-(?P<stop>\d{1,11})/(?P<end>\d{1,11})"
)


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET",))
@ensure_valid_course_key
def import_handler(request, course_key_string):
    """
    The restful handler for the import page.

    GET
        html: return html page for import page
    """
    courselike_key = CourseKey.from_string(course_key_string)
    library = isinstance(courselike_key, LibraryLocator)
    if library:
        successful_url = reverse_library_url("library_handler", courselike_key)
        courselike_module = modulestore().get_library(courselike_key)
        context_name = "context_library"
    else:
        successful_url = reverse_course_url("course_handler", courselike_key)
        courselike_module = modulestore().get_course(courselike_key)
        context_name = "context_course"

    if not has_course_author_access(request.user, courselike_key):
        raise PermissionDenied()

    return render_to_response("import.html", {
        context_name: courselike_module,
        "successful_import_redirect_url": successful_url,
        "import_status_url": reverse(
            "course_import_status_handler",
            kwargs={
                "course_key_string": unicode(courselike_key),
                "filename": "fillerName"
            }
        ),
        "import_url": reverse(
            "course_import_export_handler",
            kwargs={
                "course_key_string": unicode(courselike_key),
            }
        ),
        "library": library
    })


@ensure_csrf_cookie
@login_required
@require_http_methods(("GET",))
@ensure_valid_course_key
def export_handler(request, course_key_string):
    """
    The restful handler for the export page.

    GET
        html: return html page for import page
    """
    error = request.GET.get("error", None)
    error_message = request.GET.get("error_message", None)
    failed_module = request.GET.get("failed_module", None)
    unit = request.GET.get("unit", None)

    courselike_key = CourseKey.from_string(course_key_string)
    library = isinstance(courselike_key, LibraryLocator)
    if library:
        successful_url = reverse_library_url("library_handler", courselike_key)
        courselike_module = modulestore().get_library(courselike_key)
        context_name = "context_library"
    else:
        successful_url = reverse_course_url("course_handler", courselike_key)
        courselike_module = modulestore().get_course(courselike_key)
        context_name = "context_course"

    if not has_course_author_access(request.user, courselike_key):
        raise PermissionDenied()

    export_url = reverse(
        "course_import_export_handler",
        kwargs={
            "course_key_string": unicode(courselike_key),
        }
    ) + "?accept=application/x-tgz"

    export_url += "&{0}".format(
        urlencode({
            "redirect": reverse_course_url(
                "export_handler",
                unicode(courselike_key)
            )
        })
    )

    if unit:
        try:
            edit_unit_url = reverse_usage_url("container_handler", unit)
        except (InvalidKeyError, AttributeError):
            log.error("Invalid parent key supplied to export view: %s", unit)

            return render_to_response("export.html", {
                context_name: courselike_module,
                "export_url": export_url,
                "raw_err_msg": _(
                    "An invalid parent key was supplied: \"{supplied_key}\" "
                    "is not a valid course unit."
                ).format(supplied_key=unit),
                "library": library
            })
    else:
        edit_unit_url = ""

    if error:
        return render_to_response('export.html', {
            context_name: courselike_module,
            "export_url": export_url,
            "in_err": error,
            "unit": unit,
            "failed_module": failed_module,
            "edit_unit_url": edit_unit_url,
            "courselike_home_url": successful_url,
            "raw_err_msg": error_message,
            "library": library
        })
    else:
        return render_to_response("export.html", {
            context_name: courselike_module,
            "export_url": export_url,
            "library": library
        })
