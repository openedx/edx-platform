import warnings
warnings.warn("Importing teams.api instead of lms.djangoapps.teams.api is deprecated", stacklevel=2)

from lms.djangoapps.teams.api import *
