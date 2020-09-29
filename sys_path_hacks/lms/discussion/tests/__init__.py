from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.tests')

from lms.djangoapps.discussion.tests import *
