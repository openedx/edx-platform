"""
Learner analytics dashboard views
"""

from django.contrib.auth.decorators import login_required
from django.template.context_processors import csrf
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View

from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.features.course_experience import default_course_url_name
from util.views import ensure_valid_course_key


class LearnerAnalyticsView(View):

    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    def get(self, request, course_id):
        """
        Displays the user's bookmarks for the specified course.

        Arguments:
            request: HTTP request
            course_id (unicode): course id
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key, check_if_enrolled=True)
        course_url_name = default_course_url_name(course.id)
        course_url = reverse(course_url_name, kwargs={'course_id': unicode(course.id)})

        # Render the course bookmarks page
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'course_url': course_url,
            'disable_courseware_js': True,
            'uses_pattern_library': True,
        }
        return render_to_response('learner_analytics/dashboard.html', context)
