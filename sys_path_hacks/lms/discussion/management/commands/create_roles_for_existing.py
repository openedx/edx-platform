import warnings
warnings.warn("Importing discussion.management.commands.create_roles_for_existing instead of lms.djangoapps.discussion.management.commands.create_roles_for_existing is deprecated", stacklevel=2)

from lms.djangoapps.discussion.management.commands.create_roles_for_existing import *
