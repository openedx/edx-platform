from import_shims.warn import warn_deprecated_import

warn_deprecated_import('dashboard.management.commands.tests', 'lms.djangoapps.dashboard.management.commands.tests')

from lms.djangoapps.dashboard.management.commands.tests import *
