"""
Middleware for monitoring the LMS
"""
import time
from edx_django_utils.monitoring import set_custom_metric

# TODO:
# * Automate sync mapping definitions from ownership source-of-truth.
# * Move mappings to a plugin of edX specific customizations.
CODE_OWNER_MAPPINGS = [
    ('badges', 'programs-masters'),
    ('branding', 'engagement-website'),
    ('bulk_email', 'platform-tnl'),
    ('bulk_enroll', 'engagement-always-available'),
    ('ccx', 'platform-tnl'),
    ('certificates', 'programs-masters'),
    ('class_dashboard', 'platform-arch'),
    ('commerce', 'engagement-revenue'),
    ('course_action_state', 'platform-tnl'),
    ('course_api', 'platform-tnl'),
    ('course_blocks', 'platform-tnl'),
    ('course_goals', 'engagement-always-available'),
    ('course_modes', 'engagement-revenue'),
    ('course_wiki', 'programs-masters'),
    ('courseware', 'platform-tnl'),
    ('coursewarehistoryextended', 'platform-tnl'),
    ('dashboard', 'platform-tnl'),
    ('database_fixups', 'platform-arch'),
    ('debug', 'platform-arch'),
    ('discussion', 'programs-masters'),
    ('edxmako', 'platform-tnl'),
    ('edxnotes', 'programs-masters'),
    ('email_marketing', 'engagement-always-available'),
    ('entitlements', 'programs-masters'),
    ('experiments', 'engagement-revenue'),
    ('gating', 'engagement-revenue'),
    ('grades', 'programs-masters'),
    ('instructor_analytics', 'platform-tnl'),
    ('instructor_task', 'platform-tnl'),
    ('instructor', 'platform-tnl'),
    ('learner_dashboard', 'programs-masters'),
    ('lms_initialization', 'platform-arch'),
    ('lms_migration', 'platform-arch'),
    ('lms_xblock', 'platform-tnl'),
    ('lms.djangoapps', 'platform-tnl'),
    ('lti_provider', 'platform-tnl'),
    ('mailing', 'platform-tnl'),
    ('mobile_api', 'engagement-mobile'),
    ('notification_prefs', 'engagement-always-available'),
    ('notifier_api', 'programs-masters'),
    ('oauth2_handler', 'platform-arch'),
    ('openedx.core.djangoapps.ace_common', 'platform-tnl'),
    ('openedx.core.djangoapps.api_admin', 'platform-arch'),
    ('openedx.core.djangoapps.auth_exchange', 'platform-arch'),
    ('openedx.core.djangoapps.bookmarks', 'programs-masters'),
    ('openedx.core.djangoapps.cache_toolbox', 'platform-arch'),
    ('openedx.core.djangoapps.catalog', 'engagement-always-available'),
    ('openedx.core.djangoapps.ccxcon', 'platform-tnl'),
    ('openedx.core.djangoapps.certificates', 'programs-masters'),
    ('openedx.core.djangoapps.commerce', 'engagement-revenue'),
    ('openedx.core.djangoapps.common_initialization', 'platform-arch'),
    ('openedx.core.djangoapps.common_views', 'platform-tnl'),
    ('openedx.core.djangoapps.config_model_utils', 'platform-arch'),
    ('openedx.core.djangoapps.content_libraries', 'platform-tnl'),
    ('openedx.core.djangoapps.content.block_structure', 'platform-tnl'),
    ('openedx.core.djangoapps.content.course_overviews', 'engagement-always-available'),
    ('openedx.core.djangoapps.contentserver', 'platform-tnl'),
    ('openedx.core.djangoapps.cors_csrf', 'platform-arch'),
    ('openedx.core.djangoapps.course_groups', 'programs-masters'),
    ('openedx.core.djangoapps.coursegraph', 'platform-tnl'),
    ('openedx.core.djangoapps.crawlers', 'platform-arch'),
    ('openedx.core.djangoapps.credentials', 'programs-masters'),
    ('openedx.core.djangoapps.credit', 'programs-masters'),
    ('openedx.core.djangoapps.dark_lang', 'platform-sustaining'),
    ('openedx.core.djangoapps.debug', 'platform-arch'),
    ('openedx.core.djangoapps.django_comment_common', 'programs-masters'),
    ('openedx.core.djangoapps.embargo', 'platform-tnl'),
    ('openedx.core.djangoapps.enrollments', 'engagement-website'),
    ('openedx.core.djangoapps.geoinfo', 'platform-arch'),
    ('openedx.core.djangoapps.header_control', 'platform-arch'),
    ('openedx.core.djangoapps.heartbeat', 'platform-sre'),
    ('openedx.core.djangoapps.lang_pref', 'platform-sustaining'),
    ('openedx.core.djangoapps.models', 'platform-tnl'),
    ('openedx.core.djangoapps.monkey_patch', 'platform-arch'),
    ('openedx.core.djangoapps.oauth_dispatch', 'platform-arch'),
    ('openedx.core.djangoapps.password_policy', 'platform-sre'),
    ('openedx.core.djangoapps.plugin_api', 'platform-arch'),
    ('openedx.core.djangoapps.plugins', 'platform-arch'),
    ('openedx.core.djangoapps.profile_images', 'platform-tnl'),
    ('openedx.core.djangoapps.programs', 'programs-masters'),
    ('openedx.core.djangoapps.safe_sessions', 'platform-arch'),
    ('openedx.core.djangoapps.schedules', 'engagement-always-available'),
    ('openedx.core.djangoapps.self_paced', 'engagement-always-available'),
    ('openedx.core.djangoapps.service_status', 'platform-sre'),
    ('openedx.core.djangoapps.session_inactivity_timeout', 'platform-sustaining'),
    ('openedx.core.djangoapps.signals', 'platform-tnl'),
    ('openedx.core.djangoapps.site_configuration', 'enterprise-titans'),
    ('openedx.core.djangoapps.system_wide_roles', 'platform-sustaining'),
    ('openedx.core.djangoapps.theming', 'platform-tnl'),
    ('openedx.core.djangoapps.user_api.verification_api', 'programs-masters'),
    ('openedx.core.djangoapps.user_api', 'platform-sustaining'),
    ('openedx.core.djangoapps.user_authn', 'platform-arch'),
    ('openedx.core.djangoapps.util', 'platform-arch'),
    ('openedx.core.djangoapps.verified_track_content', 'engagement-revenue'),
    ('openedx.core.djangoapps.video_config', 'platform-sustaining'),
    ('openedx.core.djangoapps.video_pipeline', 'platform-sustaining'),
    ('openedx.core.djangoapps.waffle_utils', 'platform-arch'),
    ('openedx.core.djangoapps.xblock', 'platform-tnl'),
    ('openedx.core.djangoapps.xmodule_django', 'platform-tnl'),
    ('openedx.core.djangoapps.zendesk_proxy', 'platform-tnl'),
    ('pipeline_mako', 'platform-tnl'),
    ('program_enrollments', 'programs-masters'),
    ('rss_proxy', 'platform-arch'),
    ('shoppingcart', 'engagement-revenue'),
    ('static_replace', 'platform-arch'),
    ('static_template_view', 'platform-tnl'),
    ('staticbook', 'platform-tnl'),
    ('status', 'platform-tnl'),
    ('student', 'platform-tnl'),
    ('support', 'platform-sustaining'),
    ('survey', 'engagement-always-available'),
    ('teams', 'programs-masters'),
    ('terrain', 'platform-arch'),
    ('third_party_auth', 'platform-arch'),
    ('track', 'platform-data-de'),
    ('util', 'platform-arch'),
    ('verify_student', 'programs-masters'),
    ('xblock_django', 'platform-tnl'),
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
            set_custom_metric('view_func_module', view_func.__module__)
            for module_prefix, code_owner in CODE_OWNER_MAPPINGS:
                if view_func.__module__.startswith(module_prefix):
                    set_custom_metric('code_owner', code_owner)
                    break
        except Exception as e:
            set_custom_metric('code_owner_mapping_error', e)

        after_time = time.perf_counter()
        # Tracking the compute time enables us to alert when optimization is required.
        set_custom_metric('code_owner_mapping_time', round(after_time - before_time, 4))
