import warnings
warnings.warn("Importing badges.backends.base instead of lms.djangoapps.badges.backends.base is deprecated", stacklevel=2)

from lms.djangoapps.badges.backends.base import *
