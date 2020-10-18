from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.views.tests.test_import_export')

from cms.djangoapps.contentstore.views.tests.test_import_export import *
