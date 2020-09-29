from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'support.tests')

from lms.djangoapps.support.tests import *
