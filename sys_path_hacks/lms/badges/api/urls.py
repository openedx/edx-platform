import warnings
warnings.warn("Importing badges.api.urls instead of lms.djangoapps.badges.api.urls is deprecated", stacklevel=2)

from lms.djangoapps.badges.api.urls import *
