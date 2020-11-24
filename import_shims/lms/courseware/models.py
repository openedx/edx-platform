from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.models', 'lms.djangoapps.courseware.models')

from lms.djangoapps.courseware.models import *
