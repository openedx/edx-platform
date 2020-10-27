from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.management.commands.tests', 'lms.djangoapps.commerce.management.commands.tests')

from lms.djangoapps.commerce.management.commands.tests import *
