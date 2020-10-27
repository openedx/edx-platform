from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.user_state_client', 'lms.djangoapps.courseware.user_state_client')

from lms.djangoapps.courseware.user_state_client import *
