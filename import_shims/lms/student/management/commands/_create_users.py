from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.commands._create_users', 'common.djangoapps.student.management.commands._create_users')

from common.djangoapps.student.management.commands._create_users import *
