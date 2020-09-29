from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.date_summary')

from lms.djangoapps.courseware.date_summary import *
