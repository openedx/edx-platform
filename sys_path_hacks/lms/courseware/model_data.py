from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.model_data')

from lms.djangoapps.courseware.model_data import *
