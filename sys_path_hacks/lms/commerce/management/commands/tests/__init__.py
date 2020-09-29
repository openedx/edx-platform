from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.management.commands.tests')

from lms.djangoapps.commerce.management.commands.tests import *
