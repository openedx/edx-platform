import warnings
warnings.warn("Importing teams.waffle instead of lms.djangoapps.teams.waffle is deprecated", stacklevel=2)

from lms.djangoapps.teams.waffle import *
