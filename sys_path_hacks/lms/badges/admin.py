import warnings
warnings.warn("Importing badges.admin instead of lms.djangoapps.badges.admin is deprecated", stacklevel=2)

from lms.djangoapps.badges.admin import *
