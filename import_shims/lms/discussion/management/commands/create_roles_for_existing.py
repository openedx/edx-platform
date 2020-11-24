from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.management.commands.create_roles_for_existing', 'lms.djangoapps.discussion.management.commands.create_roles_for_existing')

from lms.djangoapps.discussion.management.commands.create_roles_for_existing import *
