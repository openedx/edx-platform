import warnings
warnings.warn("Importing teams.search_indexes instead of lms.djangoapps.teams.search_indexes is deprecated", stacklevel=2)

from lms.djangoapps.teams.search_indexes import *
