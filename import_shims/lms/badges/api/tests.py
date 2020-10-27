from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'badges.api.tests')

from lms.djangoapps.badges.api.tests import *
