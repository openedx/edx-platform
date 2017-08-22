"""
Views to render a learner's achievements.
"""

from courseware.courses import get_course_overview_with_access
from django.template.loader import render_to_string
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from student.views import get_course_certificates
from web_fragments.fragment import Fragment


class LearnerAchievementsFragmentView(EdxFragmentView):
    """
    A fragment to render a learner's achievements.
    """
    def render_to_fragment(self, request, user=None, own_profile=False, **kwargs):
        """
        Renders the current learner's achievements.
        """
        course_certificates = get_course_certificates(user)
        course_overviews = {}
        for course_key in course_certificates.keys():
            course_overview = get_course_overview_with_access(request.user, 'load', course_key)
            course_overviews[course_key] = course_overview
        context = {
            'course_certificates': course_certificates,
            'course_overviews': course_overviews,
            'own_profile': own_profile,
            'disable_courseware_js': True,
        }
        if course_certificates or own_profile:
            html = render_to_string('learner_profile/learner-achievements-fragment.html', context)
            return Fragment(html)
        else:
            return None
