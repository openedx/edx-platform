from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.serializers', 'lms.djangoapps.course_api.serializers')

from lms.djangoapps.course_api.serializers import *
