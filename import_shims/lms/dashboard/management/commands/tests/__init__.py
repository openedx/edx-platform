from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'dashboard.management.commands.tests')

from lms.djangoapps.dashboard.management.commands.tests import *
