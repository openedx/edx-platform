from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.factories', 'lms.djangoapps.courseware.tests.factories')

from lms.djangoapps.courseware.tests.factories import *
