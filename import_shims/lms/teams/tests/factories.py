from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'teams.tests.factories')

from lms.djangoapps.teams.tests.factories import *
