from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.management.commands.seed_permissions_roles', 'lms.djangoapps.discussion.management.commands.seed_permissions_roles')

from lms.djangoapps.discussion.management.commands.seed_permissions_roles import *
