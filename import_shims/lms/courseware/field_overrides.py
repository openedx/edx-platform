from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.field_overrides', 'lms.djangoapps.courseware.field_overrides')

from lms.djangoapps.courseware.field_overrides import *
