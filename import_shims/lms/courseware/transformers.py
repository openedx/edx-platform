from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.transformers', 'lms.djangoapps.courseware.transformers')

from lms.djangoapps.courseware.transformers import *
