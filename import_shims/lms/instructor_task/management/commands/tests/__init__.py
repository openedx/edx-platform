from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.management.commands.tests', 'lms.djangoapps.instructor_task.management.commands.tests')

from lms.djangoapps.instructor_task.management.commands.tests import *
