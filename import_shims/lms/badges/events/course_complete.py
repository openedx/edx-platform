from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.events.course_complete', 'lms.djangoapps.badges.events.course_complete')

from lms.djangoapps.badges.events.course_complete import *
