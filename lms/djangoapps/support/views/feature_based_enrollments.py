"""
Support tool for viewing course duration information
"""
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.views.generic import View
from edxmako.shortcuts import render_to_response
from lms.djangoapps.support.decorators import require_support_permission
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


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
            results = []

        return render_to_response('support/feature_based_enrollments.html', {
            'course_key': course_key,
            'results': results,
        })

    def _get_course_duration_info(self, course_key):
        """
        Fetch course duration information from database
        """
        results = []

        try:
            key = CourseKey.from_string(course_key)
            course = CourseOverview.objects.values('display_name').get(id=key)
            duration_config = CourseDurationLimitConfig.current(course_key=key)
            gating_config = ContentTypeGatingConfig.current(course_key=key)
            misconfigured = duration_config.enabled != gating_config.enabled

            if misconfigured:
                enabled = 'Partial'
                enabled_as_of = 'Misconfigured'
                reason = 'Misconfiguration'
            else:
                enabled = duration_config.enabled or False
                enabled_as_of = str(duration_config.enabled_as_of) if duration_config.enabled_as_of else 'N/A'
                reason = duration_config.provenances['enabled']

            data = {
                'course_id': course_key,
                'course_name': course.get('display_name'),
                'enabled': enabled,
                'enabled_as_of': enabled_as_of,
                'reason': reason,
            }
            results.append(data)

        except (ObjectDoesNotExist, InvalidKeyError):
            pass

        return results
