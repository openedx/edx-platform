from import_shims.warn import warn_deprecated_import

warn_deprecated_import('models.settings.course_grading', 'cms.djangoapps.models.settings.course_grading')

from cms.djangoapps.models.settings.course_grading import *
