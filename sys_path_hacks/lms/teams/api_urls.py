import warnings
warnings.warn("Importing teams.api_urls instead of lms.djangoapps.teams.api_urls is deprecated", stacklevel=2)

from lms.djangoapps.teams.api_urls import *
