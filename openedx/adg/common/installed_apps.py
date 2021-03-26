"""
List of common ADG installed apps.

All apps which are placed in `openedx/adg/common` must be listed here. All apps listed here
will atomically be registered in lms and cms.
"""
from openedx.adg.lms.utils.env_utils import is_testing_environment

ADG_COMMON_INSTALLED_APPS = [
    'openedx.adg.common.course_meta',
    'openedx.adg.common.mailchimp_pipeline',
]

if not is_testing_environment():
    ADG_COMMON_INSTALLED_APPS.extend(
        [
            'msp_assessment.msp_dashboard',
        ]
    )
