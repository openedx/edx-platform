from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.text_me_the_app', 'common.djangoapps.student.text_me_the_app')

from common.djangoapps.student.text_me_the_app import *
