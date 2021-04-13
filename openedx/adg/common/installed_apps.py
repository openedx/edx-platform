"""
List of common ADG installed apps.

All apps which are placed in `openedx/adg/common` must be listed here. All apps listed here
will atomically be registered in lms and cms.
"""

ADG_COMMON_INSTALLED_APPS = [
    'openedx.adg.common.course_meta',
    'openedx.adg.common.mailchimp_pipeline',
]
