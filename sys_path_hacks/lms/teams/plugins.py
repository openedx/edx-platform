import warnings
warnings.warn("Importing teams.plugins instead of lms.djangoapps.teams.plugins is deprecated", stacklevel=2)

from lms.djangoapps.teams.plugins import *
