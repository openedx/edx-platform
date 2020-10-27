from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_home_api.course_metadata.v1.serializers')

from lms.djangoapps.course_home_api.course_metadata.v1.serializers import *
