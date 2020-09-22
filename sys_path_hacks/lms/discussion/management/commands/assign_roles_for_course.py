import warnings
warnings.warn("Importing discussion.management.commands.assign_roles_for_course instead of lms.djangoapps.discussion.management.commands.assign_roles_for_course is deprecated", stacklevel=2)

from lms.djangoapps.discussion.management.commands.assign_roles_for_course import *
