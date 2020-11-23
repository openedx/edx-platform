from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.tests.test_tasks', 'cms.djangoapps.contentstore.tests.test_tasks')

from cms.djangoapps.contentstore.tests.test_tasks import *
