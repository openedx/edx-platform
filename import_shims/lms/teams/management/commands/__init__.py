from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.management.commands', 'lms.djangoapps.teams.management.commands')

from lms.djangoapps.teams.management.commands import *
