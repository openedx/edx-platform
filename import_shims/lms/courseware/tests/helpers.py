from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.tests.helpers')

from lms.djangoapps.courseware.tests.helpers import *
