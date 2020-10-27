from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.config.waffle')

from lms.djangoapps.grades.config.waffle import *
