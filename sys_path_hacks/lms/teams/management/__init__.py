import warnings
warnings.warn("Importing teams.management instead of lms.djangoapps.teams.management is deprecated", stacklevel=2)

from lms.djangoapps.teams.management import *
