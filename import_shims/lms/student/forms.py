from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.forms', 'common.djangoapps.student.forms')

from common.djangoapps.student.forms import *
