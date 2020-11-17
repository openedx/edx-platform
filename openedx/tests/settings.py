"""
Minimal Django settings for tests of common/lib.
Required in Django 1.9+ due to imports of models in stock Django apps.
"""


import sys
import tempfile

from django.utils.translation import ugettext_lazy as _
from path import Path

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

PROCTORING_BACKENDS = {
    'DEFAULT': 'mock',
    'mock': {},
    'mock_proctoring_without_rules': {},
}

FEATURES = {}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django_sites_extensions',
    'openedx.core.djangoapps.django_comment_common',
    'openedx.core.djangoapps.video_config',
    'openedx.core.djangoapps.video_pipeline',
    'openedx.core.djangoapps.bookmarks.apps.BookmarksConfig',
    'edxval',
    'lms.djangoapps.courseware',
    'lms.djangoapps.instructor_task',
    'common.djangoapps.student',
    'openedx.core.djangoapps.site_configuration',
    'lms.djangoapps.grades.apps.GradesConfig',
    'lms.djangoapps.certificates.apps.CertificatesConfig',
    'openedx.core.djangoapps.user_api',
    'common.djangoapps.course_modes.apps.CourseModesConfig',
    'lms.djangoapps.verify_student.apps.VerifyStudentConfig',
    'openedx.core.djangoapps.content_libraries',
    'openedx.core.djangoapps.dark_lang',
    'openedx.core.djangoapps.content.course_overviews.apps.CourseOverviewsConfig',
    'openedx.core.djangoapps.content.block_structure.apps.BlockStructureConfig',
    'openedx.core.djangoapps.catalog',
    'openedx.core.djangoapps.self_paced',
    'openedx.core.djangoapps.schedules.apps.SchedulesConfig',
    'openedx.core.djangoapps.theming.apps.ThemingConfig',
    'openedx.core.djangoapps.external_user_ids',
    'openedx.core.djangoapps.demographics',

    'lms.djangoapps.experiments',
    'openedx.features.content_type_gating',
    'openedx.features.course_duration_limits',
    'openedx.features.discounts',
    'milestones',
    'celery_utils',
    'waffle',
    'edx_when',
    'rest_framework_jwt',

    # Django 1.11 demands to have imported models supported by installed apps.
    'completion',
    'common.djangoapps.entitlements',
    'organizations',
)

LMS_ROOT_URL = "http://localhost:8000"

MEDIA_ROOT = tempfile.mkdtemp()

RECALCULATE_GRADES_ROUTING_KEY = 'edx.core.default'
POLICY_CHANGE_GRADES_ROUTING_KEY = 'edx.core.default'
POLICY_CHANGE_TASK_RATE_LIMIT = '300/h'


SECRET_KEY = 'insecure-secret-key'
SITE_ID = 1
SITE_NAME = "localhost"
PLATFORM_NAME = _('Your Platform Name Here')
DEFAULT_FROM_EMAIL = 'registration@example.com'
TRACK_MAX_EVENT = 50000
USE_TZ = True

RETIREMENT_SERVICE_WORKER_USERNAME = 'RETIREMENT_SERVICE_USER'
RETIRED_USERNAME_PREFIX = 'retired__user_'

PROCTORING_SETTINGS = {}

ROOT_URLCONF = None
RUN_BLOCKSTORE_TESTS = False

# Software Secure request retry settings
# Time in seconds before a retry of the task should be 60 mints.
SOFTWARE_SECURE_REQUEST_RETRY_DELAY = 60 * 60
# Maximum of 6 retries before giving up.
SOFTWARE_SECURE_RETRY_MAX_ATTEMPTS = 6
