from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.tests.test_crud', 'cms.djangoapps.contentstore.tests.test_crud')

from cms.djangoapps.contentstore.tests.test_crud import *
