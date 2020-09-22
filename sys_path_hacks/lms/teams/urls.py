import warnings
warnings.warn("Importing teams.urls instead of lms.djangoapps.teams.urls is deprecated", stacklevel=2)

from lms.djangoapps.teams.urls import *
