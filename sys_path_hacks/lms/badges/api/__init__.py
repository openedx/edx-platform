import warnings
warnings.warn("Importing badges.api instead of lms.djangoapps.badges.api is deprecated", stacklevel=2)

from lms.djangoapps.badges.api import *
