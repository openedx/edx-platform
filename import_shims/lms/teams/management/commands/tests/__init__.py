from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.management.commands.tests', 'lms.djangoapps.teams.management.commands.tests')

from lms.djangoapps.teams.management.commands.tests import *
