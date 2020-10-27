from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'teams.serializers')

from lms.djangoapps.teams.serializers import *
