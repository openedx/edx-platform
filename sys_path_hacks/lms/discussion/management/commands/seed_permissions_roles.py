import warnings
warnings.warn("Importing discussion.management.commands.seed_permissions_roles instead of lms.djangoapps.discussion.management.commands.seed_permissions_roles is deprecated", stacklevel=2)

from lms.djangoapps.discussion.management.commands.seed_permissions_roles import *
