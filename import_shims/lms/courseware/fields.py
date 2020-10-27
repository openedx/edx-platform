from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.fields')

from lms.djangoapps.courseware.fields import *
