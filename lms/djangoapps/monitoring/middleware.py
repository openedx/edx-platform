"""
Middleware for monitoring the LMS
"""
import time
from edx_django_utils.monitoring import set_custom_metric


# TODO:
# * Automate sync mapping definitions from ownership source-of-truth.
# * Move mappings to a plugin of edX specific customizations.
CODE_OWNER_MAPPINGS = [
    ('course_action_state', 'platform-tnl'),
    ('course_modes', 'engagement-revenue'),
    ('database_fixups', 'platform-arch'),
    ('edxmako', 'platform-tnl'),
    ('entitlements', 'programs-masters'),
    ('lms.djangoapps.badges', 'programs-masters'),
    ('lms.djangoapps.branding', 'engagement-website'),
    ('lms.djangoapps.bulk_email', 'platform-tnl'),
    ('lms.djangoapps.bulk_enroll', 'engagement-always-available'),
    ('lms.djangoapps.ccx', 'platform-tnl'),
    ('lms.djangoapps.certificates', 'programs-masters'),
    ('lms.djangoapps.class_dashboard', 'platform-arch'),
    ('lms.djangoapps.commerce', 'engagement-revenue'),
    ('lms.djangoapps.course_api', 'platform-tnl'),
    ('lms.djangoapps.course_blocks', 'platform-tnl'),
    ('lms.djangoapps.course_goals', 'engagement-always-available'),
    ('lms.djangoapps.course_wiki', 'programs-masters'),
    ('lms.djangoapps.courseware', 'platform-tnl'),
    ('lms.djangoapps.coursewarehistoryextended', 'platform-tnl'),
    ('lms.djangoapps.dashboard', 'platform-tnl'),
    ('lms.djangoapps.debug', 'platform-arch'),
    ('lms.djangoapps.discussion', 'programs-masters'),
    ('lms.djangoapps.edxnotes', 'programs-masters'),
    ('lms.djangoapps.email_marketing', 'engagement-always-available'),
    ('lms.djangoapps.experiments', 'engagement-revenue'),
    ('lms.djangoapps.gating', 'engagement-revenue'),
    ('lms.djangoapps.grades', 'programs-masters'),
    ('lms.djangoapps.instructor_analytics', 'platform-tnl'),
    ('lms.djangoapps.instructor_task', 'platform-tnl'),
    ('lms.djangoapps.instructor', 'platform-tnl'),
    ('lms.djangoapps.learner_dashboard', 'programs-masters'),
    ('lms.djangoapps.lms_initialization', 'platform-arch'),
    ('lms.djangoapps.lms_migration', 'platform-arch'),
    ('lms.djangoapps.lms_xblock', 'platform-tnl'),
    ('lms.djangoapps.lti_provider', 'platform-tnl'),
    ('lms.djangoapps.mailing', 'platform-tnl'),
    ('lms.djangoapps.mobile_api', 'engagement-mobile'),
    ('lms.djangoapps.notification_prefs', 'engagement-always-available'),
    ('lms.djangoapps.notifier_api', 'programs-masters'),
    ('lms.djangoapps.oauth2_handler', 'platform-arch'),
    ('lms.djangoapps.program_enrollments', 'programs-masters'),
    ('lms.djangoapps.rss_proxy', 'platform-arch'),
    ('lms.djangoapps.shoppingcart', 'engagement-revenue'),
    ('lms.djangoapps.static_template_view', 'platform-tnl'),
    ('lms.djangoapps.staticbook', 'platform-tnl'),
    ('lms.djangoapps.support', 'platform-sustaining'),
    ('lms.djangoapps.survey', 'engagement-always-available'),
    ('lms.djangoapps.teams', 'programs-masters'),
    ('lms.djangoapps.tests', 'platform-arch'),
    ('lms.djangoapps.verify_student', 'programs-masters'),
    ('lms.djangoapps', 'platform-tnl'),
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
    ('static_replace', 'platform-arch'),
    ('status', 'platform-tnl'),
    ('student', 'platform-tnl'),
    ('terrain', 'platform-arch'),
    ('third_party_auth', 'platform-arch'),
    ('track', 'platform-data-de'),
    ('util', 'platform-arch'),
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
