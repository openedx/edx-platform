from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.signals.handlers')

from lms.djangoapps.grades.signals.handlers import *
