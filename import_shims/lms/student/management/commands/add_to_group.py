from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands.add_to_group', 'common.djangoapps.student.management.commands.add_to_group')

from common.djangoapps.student.management.commands.add_to_group import *
