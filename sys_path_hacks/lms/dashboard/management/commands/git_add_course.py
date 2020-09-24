import warnings
warnings.warn("Importing dashboard.management.commands.git_add_course instead of lms.djangoapps.dashboard.management.commands.git_add_course is deprecated", stacklevel=2)

from lms.djangoapps.dashboard.management.commands.git_add_course import *
