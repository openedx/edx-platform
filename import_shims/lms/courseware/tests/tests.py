from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.tests', 'lms.djangoapps.courseware.tests.tests')

from lms.djangoapps.courseware.tests.tests import *
