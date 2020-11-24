from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests', 'lms.djangoapps.courseware.tests')

from lms.djangoapps.courseware.tests import *
