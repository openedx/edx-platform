from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands.bulk_unenroll', 'common.djangoapps.student.management.commands.bulk_unenroll')

from common.djangoapps.student.management.commands.bulk_unenroll import *
