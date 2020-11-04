from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands.manage_group', 'common.djangoapps.student.management.commands.manage_group')

from common.djangoapps.student.management.commands.manage_group import *
