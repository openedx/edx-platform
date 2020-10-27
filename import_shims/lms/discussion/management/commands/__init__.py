from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.management.commands', 'lms.djangoapps.discussion.management.commands')

from lms.djangoapps.discussion.management.commands import *
