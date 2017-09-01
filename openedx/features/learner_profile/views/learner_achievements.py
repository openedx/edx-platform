"""
Views to render a learner's achievements.
"""

from courseware.courses import get_course_overview_with_access
from django.template.loader import render_to_string
from lms.djangoapps.certificates import api as certificate_api
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from web_fragments.fragment import Fragment


class LearnerAchievementsFragmentView(EdxFragmentView):
    """
    A fragment to render a learner's achievements.
    """
    def render_to_fragment(self, request, username=None, own_profile=False, **kwargs):
        """
        Renders the current learner's achievements.
        """
        course_certificates = self._get_ordered_certificates_for_user(request, username)
        context = {
            'course_certificates': course_certificates,
            'own_profile': own_profile,
            'disable_courseware_js': True,
        }
        if course_certificates or own_profile:
            html = render_to_string('learner_profile/learner-achievements-fragment.html', context)
            return Fragment(html)
        else:
            return None

    def _get_ordered_certificates_for_user(self, request, username):
        """
        Returns a user's certificates sorted by course name.
        """
        course_certificates = certificate_api.get_certificates_for_user(username)
        for course_certificate in course_certificates:
            course_key = course_certificate['course_key']
            course_overview = get_course_overview_with_access(request.user, 'load', course_key)
            course_certificate['course'] = course_overview
        course_certificates.sort(key=lambda certificate: certificate['course'].display_name_with_default)
        return course_certificates
