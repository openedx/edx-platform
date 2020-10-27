from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.management.commands.show_permissions', 'lms.djangoapps.discussion.management.commands.show_permissions')

from lms.djangoapps.discussion.management.commands.show_permissions import *
