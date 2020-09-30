from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'models.settings.course_grading')

from cms.djangoapps.models.settings.course_grading import *
