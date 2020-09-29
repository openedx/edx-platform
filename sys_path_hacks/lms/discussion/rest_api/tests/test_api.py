from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.rest_api.tests.test_api')

from lms.djangoapps.discussion.rest_api.tests.test_api import *
