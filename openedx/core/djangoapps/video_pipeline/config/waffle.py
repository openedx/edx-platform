"""
This module contains configuration settings via waffle flags
for the Video Pipeline app.
"""

from edx_toggles.toggles import WaffleFlag, WaffleFlagNamespace
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# Videos Namespace
WAFFLE_NAMESPACE = 'videos'

# .. toggle_name: videos.deprecate_youtube
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag telling whether youtube is deprecated. When enabled, videos are no longer uploaded
#   to YouTube as part of the video pipeline.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2018-08-03
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/18765
DEPRECATE_YOUTUBE = 'deprecate_youtube'
# .. toggle_name: videos.enable_devstack_video_uploads
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: When enabled, use Multi-Factor Authentication (MFA) for authenticating to AWS. These short-
#   lived access tokens are well suited for development (probably?). [At the time of annotation, the exact consequences
#   of enabling this feature toggle are uncertain.]
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2020-03-12
# .. toggle_target_removal_date: None
# .. toggle_warnings: Enabling this feature requires that the ROLE_ARN, MFA_SERIAL_NUMBER, MFA_TOKEN settings are
#   properly defined.
# .. toggle_tickets: https://github.com/edx/edx-platform/pull/23375
ENABLE_DEVSTACK_VIDEO_UPLOADS = 'enable_devstack_video_uploads'
ENABLE_VEM_PIPELINE = 'enable_vem_pipeline'


def waffle_flags():
    """
    Returns the namespaced, cached, audited Waffle flags dictionary for Videos.
    """
    namespace = WaffleFlagNamespace(name=WAFFLE_NAMESPACE, log_prefix=u'Videos: ')
    return {
        DEPRECATE_YOUTUBE: CourseWaffleFlag(
            waffle_namespace=namespace,
            flag_name=DEPRECATE_YOUTUBE,
            module_name=__name__,
        ),
        ENABLE_DEVSTACK_VIDEO_UPLOADS: WaffleFlag(
            waffle_namespace=namespace,
            flag_name=ENABLE_DEVSTACK_VIDEO_UPLOADS,
            module_name=__name__,
        ),
        ENABLE_VEM_PIPELINE: CourseWaffleFlag(
            waffle_namespace=namespace,
            flag_name=ENABLE_VEM_PIPELINE,
            module_name=__name__,
        )
    }
