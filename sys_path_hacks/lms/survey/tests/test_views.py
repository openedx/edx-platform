from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'survey.tests.test_views')

from lms.djangoapps.survey.tests.test_views import *
