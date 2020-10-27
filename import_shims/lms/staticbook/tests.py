from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'staticbook.tests')

from lms.djangoapps.staticbook.tests import *
