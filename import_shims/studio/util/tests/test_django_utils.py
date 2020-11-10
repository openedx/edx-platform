from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.tests.test_django_utils', 'common.djangoapps.util.tests.test_django_utils')

from common.djangoapps.util.tests.test_django_utils import *
