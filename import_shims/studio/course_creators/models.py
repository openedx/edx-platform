from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_creators.models', 'cms.djangoapps.course_creators.models')

from cms.djangoapps.course_creators.models import *
