from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands.create_random_users', 'common.djangoapps.student.management.commands.create_random_users')

from common.djangoapps.student.management.commands.create_random_users import *
