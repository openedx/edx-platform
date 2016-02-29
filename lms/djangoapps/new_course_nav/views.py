from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from edxmako.shortcuts import render_to_response

from opaque_keys.edx.keys import CourseKey

from courseware.courses import get_course_with_access


# TODO: extract base generic TemplateView class which attaches
# 'course', 'user', and other key fields to the context dict in
# 'get_context_data' by default.
class NewCourseNavView(TemplateView):
    template_name = "new_course_nav/index.html"

    def get_context_data(self, course_id, **kwargs):
        context = super(NewCourseNavView, self).get_context_data(**kwargs)
        user = self.request.user
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(user, "load", course_key)
        context['course'] = course
        context['course_api_url'] = reverse('course-detail', args=[course_id])
        context['course_blocks_api_url'] = reverse('blocks_in_course')
        return context
