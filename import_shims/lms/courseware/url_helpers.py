from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.url_helpers', 'lms.djangoapps.courseware.url_helpers')

from lms.djangoapps.courseware.url_helpers import *
