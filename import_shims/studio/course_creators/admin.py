from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_creators.admin', 'cms.djangoapps.course_creators.admin')

from cms.djangoapps.course_creators.admin import *
