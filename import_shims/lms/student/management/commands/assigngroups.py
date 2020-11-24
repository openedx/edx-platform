from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands.assigngroups', 'common.djangoapps.student.management.commands.assigngroups')

from common.djangoapps.student.management.commands.assigngroups import *
