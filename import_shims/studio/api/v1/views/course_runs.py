from import_shims.warn import warn_deprecated_import

warn_deprecated_import('api.v1.views.course_runs', 'cms.djangoapps.api.v1.views.course_runs')

from cms.djangoapps.api.v1.views.course_runs import *
