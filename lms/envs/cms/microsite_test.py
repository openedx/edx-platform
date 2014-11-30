"""
This is a localdev test for the Microsite processing pipeline
"""
# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from .dev import *
from ..dev import ENV_ROOT, FEATURES


MICROSITE_CONFIGURATION = {
    "openedx": {
        "domain_prefix": "openedx",
        "university": "openedx",
        "platform_name": "Open edX",
        "logo_image_url": "openedx/images/header-logo.png",
        "email_from_address": "openedx@edx.org",
        "payment_support_email": "openedx@edx.org",
        "ENABLE_MKTG_SITE": False,
        "SITE_NAME": "openedx.localhost",
        "course_org_filter": "CDX",
        "course_about_show_social_links": False,
        "css_overrides_file": "openedx/css/openedx.css",
        "show_partners": False,
        "show_homepage_promo_video": False,
        "course_index_overlay_text": "Explore free courses from leading universities.",
        "course_index_overlay_logo_file": "openedx/images/header-logo.png",
        "homepage_overlay_html": "<h1>Take an Open edX Course</h1>"
    }
}

MICROSITE_ROOT_DIR = ENV_ROOT / 'edx-microsite'

# pretend we are behind some marketing site, we want to be able to assert that the Microsite config values override
# this global setting
FEATURES['ENABLE_MKTG_SITE'] = True
FEATURES['USE_MICROSITES'] = True
