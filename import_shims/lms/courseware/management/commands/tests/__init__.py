from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.management.commands.tests', 'lms.djangoapps.courseware.management.commands.tests')

from lms.djangoapps.courseware.management.commands.tests import *
