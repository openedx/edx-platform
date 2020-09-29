from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'badges.api.serializers')

from lms.djangoapps.badges.api.serializers import *
