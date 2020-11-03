"""
Django settings for use when generating API documentation.
Basically the LMS devstack settings plus a few items needed to successfully
import all the Studio code.
"""


import os

if os.environ['EDX_PLATFORM_SETTINGS'] == 'devstack_docker':
    from lms.envs.devstack_docker import *
    from cms.envs.devstack_docker import (
        ADVANCED_PROBLEM_TYPES,
        COURSE_IMPORT_EXPORT_STORAGE,
        LIBRARY_AUTHORING_MICROFRONTEND_URL,
        SCRAPE_YOUTUBE_THUMBNAILS_JOB_QUEUE,
        VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE,
        UPDATE_SEARCH_INDEX_JOB_QUEUE,
    )
else:
    from lms.envs.devstack import *
    from cms.envs.devstack import (
        ADVANCED_PROBLEM_TYPES,
        COURSE_IMPORT_EXPORT_STORAGE,
        LIBRARY_AUTHORING_MICROFRONTEND_URL,
        SCRAPE_YOUTUBE_THUMBNAILS_JOB_QUEUE,
        VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE,
        UPDATE_SEARCH_INDEX_JOB_QUEUE,
    )

# Turn on all the boolean feature flags, so that conditionally included
# API endpoints will be found.
for key, value in FEATURES.items():
    if value is False:
        FEATURES[key] = True

# Settings that will fail if we enable them, and we don't need them for docs anyway.
FEATURES['RUN_AS_ANALYTICS_SERVER_ENABLED'] = False

INSTALLED_APPS.extend([
    'contentstore.apps.ContentstoreConfig',
    'cms.djangoapps.course_creators',
    'xblock_config.apps.XBlockConfig',
    'user_tasks',
    'lms.djangoapps.lti_provider'
])
