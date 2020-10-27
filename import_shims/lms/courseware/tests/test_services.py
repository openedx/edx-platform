from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_services', 'lms.djangoapps.courseware.tests.test_services')

from lms.djangoapps.courseware.tests.test_services import *
