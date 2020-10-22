from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.tests.test_courseware_index')

from cms.djangoapps.contentstore.tests.test_courseware_index import *
