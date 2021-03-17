"""
Support tool for viewing course duration information
"""


from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.views.generic import View
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.edxmako.shortcuts import render_to_response
from lms.djangoapps.support.decorators import require_support_permission
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig


class FeatureBasedEnrollmentsSupportView(View):
    """
    View for listing course duration settings for
    support team.
    """
    @method_decorator(require_support_permission)
    def get(self, request):
        """
        Render the course duration tool view.
        """
        course_key = request.GET.get('course_key', '')

        if course_key:
            results = self._get_course_duration_info(course_key)
        else:
            results = {}

        return render_to_response('support/feature_based_enrollments.html', {
            'course_key': course_key,
            'results': results,
        })

    def _get_course_duration_info(self, course_key):
        """
        Fetch course duration information from database
        """
        try:
            key = CourseKey.from_string(course_key)
            course = CourseOverview.objects.values('display_name').get(id=key)
            duration_config = CourseDurationLimitConfig.current(course_key=key)
            gating_config = ContentTypeGatingConfig.current(course_key=key)
            duration_enabled = CourseDurationLimitConfig.enabled_for_course(course_key=key)
            gating_enabled = ContentTypeGatingConfig.enabled_for_course(course_key=key)

            gating_dict = {
                'enabled': gating_enabled,
                'enabled_as_of': str(gating_config.enabled_as_of) if gating_config.enabled_as_of else 'N/A',
                'reason': gating_config.provenances['enabled'].value
            }
            duration_dict = {
                'enabled': duration_enabled,
                'enabled_as_of': str(duration_config.enabled_as_of) if duration_config.enabled_as_of else 'N/A',
                'reason': duration_config.provenances['enabled'].value
            }

            return {
                'course_id': course_key,
                'course_name': course.get('display_name'),
                'gating_config': gating_dict,
                'duration_config': duration_dict,
            }

        except (ObjectDoesNotExist, InvalidKeyError):
            return {}
