from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.management.commands.tests.test_migrate_to_split')

from cms.djangoapps.contentstore.management.commands.tests.test_migrate_to_split import *
