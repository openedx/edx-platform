import warnings
warnings.warn("Importing dashboard.management.commands instead of lms.djangoapps.dashboard.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.dashboard.management.commands import *
