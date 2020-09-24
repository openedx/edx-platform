import warnings
warnings.warn("Importing teams.csv instead of lms.djangoapps.teams.csv is deprecated", stacklevel=2)

from lms.djangoapps.teams.csv import *
