from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_creators.views', 'cms.djangoapps.course_creators.views')

from cms.djangoapps.course_creators.views import *
