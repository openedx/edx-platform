from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'badges.tests.factories')

from lms.djangoapps.badges.tests.factories import *
