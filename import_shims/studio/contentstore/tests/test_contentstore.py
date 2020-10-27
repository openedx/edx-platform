from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.tests.test_contentstore', 'cms.djangoapps.contentstore.tests.test_contentstore')

from cms.djangoapps.contentstore.tests.test_contentstore import *
