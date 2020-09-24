import warnings
warnings.warn("Importing teams instead of lms.djangoapps.teams is deprecated", stacklevel=2)

from lms.djangoapps.teams import *
