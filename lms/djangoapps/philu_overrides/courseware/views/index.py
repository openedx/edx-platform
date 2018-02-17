"""
View for Courseware Index
"""
# pylint: disable=attribute-defined-outside-init
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import redirect

import logging
import urllib

from opaque_keys.edx.keys import CourseKey

from courseware.views.index import CoursewareIndex
from util.views import ensure_valid_course_key
from xmodule.modulestore.django import modulestore
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import get_course_with_access
from lms.djangoapps.courseware.exceptions import Redirect


log = logging.getLogger("edx.courseware.views.index")
TEMPLATE_IMPORTS = {'urllib': urllib}
CONTENT_DEPTH = 2


class CustomCoursewareIndex(CoursewareIndex):
    """
    View class for the Courseware page.
    """
    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    def get(self, request, course_id, chapter=None, section=None, position=None):
        """
        Displays courseware accordion and associated content.  If course, chapter,
        and section are all specified, renders the page, or returns an error if they
        are invalid.

        If section is not specified, displays the accordion opened to the right
        chapter.

        If neither chapter or section are specified, displays the user's most
        recent chapter, or the first chapter if this is the user's first visit.

        Arguments:
            request: HTTP request
            course_id (unicode): course id
            chapter (unicode): chapter url_name
            section (unicode): section url_name
            position (unicode): position in module, eg of <sequential> module
        """
        self.course_key = CourseKey.from_string(course_id)
        self.request = request
        self.original_chapter_url_name = chapter
        self.original_section_url_name = section
        self.chapter_url_name = chapter
        self.section_url_name = section
        self.position = position
        self.chapter, self.section = None, None
        self.url = request.path

        try:
            self._init_new_relic()
            self._clean_position()
            with modulestore().bulk_operations(self.course_key):
                self.course = get_course_with_access(request.user, 'load', self.course_key, depth=CONTENT_DEPTH)
                self.is_staff = has_access(request.user, 'staff', self.course)
                self._setup_masquerade_for_effective_user()
                return self._get()
        except Redirect as redirect_error:
            return redirect(redirect_error.url)
        except UnicodeEncodeError:
            raise Http404("URL contains Unicode characters")
        except Http404:
            # let it propagate
            return redirect("404")
        except Exception:  # pylint: disable=broad-except
            return self._handle_unexpected_error()


    def _redirect_if_not_requested_section(self):
        """
        If the resulting section and chapter are different from what was initially
        requested, redirect back to the index page, but with an updated URL that includes
        the correct section and chapter values.  We do this so that our analytics events
        and error logs have the appropriate URLs.
        """
        if (
                self.chapter.url_name != self.original_chapter_url_name or
                (self.original_section_url_name and self.section.url_name != self.original_section_url_name)
        ):
            raise Redirect(
                reverse(
                    'courseware_section',
                    kwargs={
                        'course_id': unicode(self.course_key),
                        'chapter': self.chapter.url_name,
                        'section': self.section.url_name,
                    },
                )
            )