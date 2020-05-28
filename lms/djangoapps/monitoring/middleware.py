"""
Middleware for monitoring the LMS
"""
import time
from edx_django_utils.monitoring import set_custom_metric
from enum import Enum

class CodeOwner(Enum):
    platform_arch = 'platform-arch'
    platform_sustaining = 'platform-sustaining'
    platform_tnl = 'platform-tnl'
    programs_masters = 'programs-masters'

# Initial implementation maps high priority paths.
# TODO:
# * Generate mapping definitions from ownership source-of-truth.
# * Move mappings to a plugin of edX specific customizations.
CODE_OWNER_MAPPINGS = [
    ('common.djangoapps.third_party_auth.', CodeOwner.platform_arch),
    ('openedx.core.djangoapps.auth_exchange.', CodeOwner.platform_arch),
    ('openedx.core.djangoapps.content.block_structure.', CodeOwner.platform_tnl),
    ('openedx.core.djangoapps.oauth_dispatch.', CodeOwner.platform_arch),
    ('openedx.core.djangoapps.user_authn.', CodeOwner.platform_arch),
    ('openedx.core.djangoapps.video_config.', CodeOwner.platform_sustaining),
    ('openedx.core.djangoapps.video_pipeline.', CodeOwner.platform_sustaining),
    ('lms.djangoapps.course_api.', CodeOwner.platform_tnl),
    ('lms.djangoapps.course_blocks.', CodeOwner.platform_tnl),
    ('lms.djangoapps.courseware.', CodeOwner.platform_tnl),
    ('lms.djangoapps.grades.', CodeOwner.programs_masters),
    ('lms.djangoapps.program_enrollments.', CodeOwner.programs_masters),
]


class CodeOwnerMetricMiddleware:
    """
    Django middleware object to set custom metric for the owner of each view.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Set custom metric for the code_owner of the view.
        """
        before_time = time.perf_counter()
        try:
            set_custom_metric('code_owner', 'unknown')
            for module_prefix, code_owner in CODE_OWNER_MAPPINGS:
                if view_func.__module__.startswith(module_prefix):
                    set_custom_metric('code_owner', code_owner.value)
                    break
        except Exception as e:
            set_custom_metric('code_owner_mapping_error', e)

        after_time = time.perf_counter()
        # Tracking the compute time enables us to alert when optimization is required.
        set_custom_metric('code_owner_mapping_time', round(after_time - before_time, 4))
