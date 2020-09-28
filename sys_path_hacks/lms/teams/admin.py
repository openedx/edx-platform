import warnings
warnings.warn("Importing teams.admin instead of lms.djangoapps.teams.admin is deprecated", stacklevel=2)

from lms.djangoapps.teams.admin import *
