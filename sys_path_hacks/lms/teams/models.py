import warnings
warnings.warn("Importing teams.models instead of lms.djangoapps.teams.models is deprecated", stacklevel=2)

from lms.djangoapps.teams.models import *
