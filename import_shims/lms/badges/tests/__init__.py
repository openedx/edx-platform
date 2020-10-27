from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'badges.tests')

from lms.djangoapps.badges.tests import *
