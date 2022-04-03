"""
Django settings for use when generating API documentation.
Basically the LMS devstack settings plus a few items needed to successfully
import all the Studio code.
"""


import os

from openedx.core.lib.derived import derive_settings

from lms.envs.common import *  # lint-amnesty, pylint: disable=wildcard-import
from cms.envs.common import (  # lint-amnesty, pylint: disable=unused-import
    ADVANCED_PROBLEM_TYPES,
    COURSE_IMPORT_EXPORT_STORAGE,
    GIT_EXPORT_DEFAULT_IDENT,
    LIBRARY_AUTHORING_MICROFRONTEND_URL,
    SCRAPE_YOUTUBE_THUMBNAILS_JOB_QUEUE,
    VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE,
    UPDATE_SEARCH_INDEX_JOB_QUEUE,
    FRONTEND_REGISTER_URL,
)

# Turn on all the boolean feature flags, so that conditionally included
# API endpoints will be found.
for key, value in FEATURES.items():
    if value is False:
        FEATURES[key] = True

# Settings that will fail if we enable them, and we don't need them for docs anyway.
FEATURES['RUN_AS_ANALYTICS_SERVER_ENABLED'] = False
FEATURES['ENABLE_SOFTWARE_SECURE_FAKE'] = False
FEATURES['ENABLE_MKTG_SITE'] = False

INSTALLED_APPS.extend([
    'cms.djangoapps.contentstore.apps.ContentstoreConfig',
    'cms.djangoapps.course_creators',
    'cms.djangoapps.xblock_config.apps.XBlockConfig',
    'lms.djangoapps.lti_provider',
    'user_tasks',
])


COMMON_TEST_DATA_ROOT = ''

derive_settings(__name__)
