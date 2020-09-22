import warnings
warnings.warn("Importing teams.management.commands instead of lms.djangoapps.teams.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.teams.management.commands import *
