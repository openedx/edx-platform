from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.management.commands.tests.test_create_course')

from cms.djangoapps.contentstore.management.commands.tests.test_create_course import *
