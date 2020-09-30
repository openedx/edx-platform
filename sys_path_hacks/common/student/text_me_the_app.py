from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.text_me_the_app')

from common.djangoapps.student.text_me_the_app import *
