from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.settings.test')

from lms.djangoapps.grades.settings.test import *
