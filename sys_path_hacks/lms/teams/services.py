import warnings
warnings.warn("Importing teams.services instead of lms.djangoapps.teams.services is deprecated", stacklevel=2)

from lms.djangoapps.teams.services import *
