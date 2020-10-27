from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'course_creators.views')

from cms.djangoapps.course_creators.views import *
