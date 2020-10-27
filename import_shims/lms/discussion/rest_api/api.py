from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.rest_api.api')

from lms.djangoapps.discussion.rest_api.api import *
