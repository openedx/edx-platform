from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.management.commands.seed_permissions_roles')

from lms.djangoapps.discussion.management.commands.seed_permissions_roles import *
