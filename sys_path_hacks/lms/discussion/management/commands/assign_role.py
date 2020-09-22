import warnings
warnings.warn("Importing discussion.management.commands.assign_role instead of lms.djangoapps.discussion.management.commands.assign_role is deprecated", stacklevel=2)

from lms.djangoapps.discussion.management.commands.assign_role import *
