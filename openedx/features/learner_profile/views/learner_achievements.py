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
        raw_course_certificates = get_course_certificates(user)
        course_certificates = {}
        for course_key in raw_course_certificates.keys():
            course_certificate = raw_course_certificates[course_key].copy()
            certificate_url = course_certificate.get('cert_web_view_url', None)
            if not certificate_url:
                certificate_url = course_certificate.get('linked_in_url', None)
            course_overview = get_course_overview_with_access(request.user, 'load', course_key)
            course_certificate['url'] = certificate_url
            course_certificate['course'] = course_overview
            course_certificates[course_key] = course_certificate
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
