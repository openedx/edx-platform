"""
Minimal Django settings for tests of common/lib.
Required in Django 1.9+ due to imports of models in stock Django apps.
"""

from __future__ import absolute_import, unicode_literals

import sys
import tempfile

from path import Path

# TODO: Remove the rest of the sys.path modification here and in (cms|lms)/envs/common.py
REPO_ROOT = Path(__file__).abspath().dirname().dirname().dirname()  # /edx-platform/
sys.path.append(REPO_ROOT / 'common' / 'djangoapps')
sys.path.append(REPO_ROOT / 'lms' / 'djangoapps')

ALL_LANGUAGES = []

BLOCK_STRUCTURES_SETTINGS = dict(
    COURSE_PUBLISH_TASK_DELAY=30,
    TASK_DEFAULT_RETRY_DELAY=30,
    TASK_MAX_RETRIES=5,
)

COURSE_KEY_PATTERN = r'(?P<course_key_string>[^/+]+(/|\+)[^/+]+(/|\+)[^/?]+)'
COURSE_ID_PATTERN = COURSE_KEY_PATTERN.replace('course_key_string', 'course_id')
USAGE_KEY_PATTERN = r'(?P<usage_key_string>(?:i4x://?[^/]+/[^/]+/[^/]+/[^@]+(?:@[^/]+)?)|(?:[^/]+))'


COURSE_MODE_DEFAULTS = {
    'bulk_sku': None,
    'currency': 'usd',
    'description': None,
    'expiration_datetime': None,
    'min_price': 0,
    'name': 'Audit',
    'sku': None,
    'slug': 'audit',
    'suggested_prices': '',
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'default.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

FEATURES = {}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'djcelery',
    'openedx.core.djangoapps.video_config',
    'openedx.core.djangoapps.video_pipeline',
    'openedx.core.djangoapps.bookmarks.apps.BookmarksConfig',
    'edxval',
    'courseware',
    'student',
    'openedx.core.djangoapps.site_configuration',
    'lms.djangoapps.certificates.apps.CertificatesConfig',
    'openedx.core.djangoapps.user_api',
    'course_modes.apps.CourseModesConfig',
    'lms.djangoapps.verify_student.apps.VerifyStudentConfig',
    'openedx.core.djangoapps.dark_lang',
    'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig',
    'openedx.core.djangoapps.content.block_structure.apps.BlockStructureConfig',
    'openedx.core.djangoapps.catalog',
    'openedx.core.djangoapps.self_paced',
    'experiments',
    'openedx.features.content_type_gating',
    'openedx.features.course_duration_limits',
    'milestones',
    'celery_utils',
    'waffle',

    # Django 1.11 demands to have imported models supported by installed apps.
    'completion',
)

LMS_ROOT_URL = 'http://localhost:8000'

MEDIA_ROOT = tempfile.mkdtemp()

MICROSITE_BACKEND = 'microsite_configuration.backends.filebased.FilebasedMicrositeBackend'
MICROSITE_TEMPLATE_BACKEND = 'microsite_configuration.backends.filebased.FilebasedMicrositeTemplateBackend'

SECRET_KEY = 'insecure-secret-key'
SITE_ID = 1

TRACK_MAX_EVENT = 50000

USE_TZ = True

RETIREMENT_SERVICE_WORKER_USERNAME = 'RETIREMENT_SERVICE_USER'
RETIRED_USERNAME_PREFIX = 'retired__user_'
