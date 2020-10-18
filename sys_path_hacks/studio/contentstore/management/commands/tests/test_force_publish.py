from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.management.commands.tests.test_force_publish')

from cms.djangoapps.contentstore.management.commands.tests.test_force_publish import *
