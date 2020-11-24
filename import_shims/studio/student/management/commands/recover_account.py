from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands.recover_account', 'common.djangoapps.student.management.commands.recover_account')

from common.djangoapps.student.management.commands.recover_account import *
