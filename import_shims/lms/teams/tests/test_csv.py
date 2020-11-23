from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.tests.test_csv', 'lms.djangoapps.teams.tests.test_csv')

from lms.djangoapps.teams.tests.test_csv import *
