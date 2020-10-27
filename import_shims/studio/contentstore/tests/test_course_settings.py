from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.tests.test_course_settings')

from cms.djangoapps.contentstore.tests.test_course_settings import *
