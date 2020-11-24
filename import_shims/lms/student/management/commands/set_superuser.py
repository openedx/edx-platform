from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands.set_superuser', 'common.djangoapps.student.management.commands.set_superuser')

from common.djangoapps.student.management.commands.set_superuser import *
