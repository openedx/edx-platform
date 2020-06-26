"""
This module contains configuration settings via waffle flags
for the Video Pipeline app.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag, WaffleFlag, WaffleFlagNamespace

# Videos Namespace
WAFFLE_NAMESPACE = 'videos'

# Waffle flag telling whether youtube is deprecated.
DEPRECATE_YOUTUBE = 'deprecate_youtube'
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
            flag_name=DEPRECATE_YOUTUBE
        ),
        ENABLE_DEVSTACK_VIDEO_UPLOADS: WaffleFlag(
            waffle_namespace=namespace,
            flag_name=ENABLE_DEVSTACK_VIDEO_UPLOADS,
            flag_undefined_default=False
        ),
        ENABLE_VEM_PIPELINE: CourseWaffleFlag(
            waffle_namespace=namespace,
            flag_name=ENABLE_VEM_PIPELINE,
            flag_undefined_default=False
        )
    }
