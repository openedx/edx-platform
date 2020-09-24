import warnings
warnings.warn("Importing badges.backends instead of lms.djangoapps.badges.backends is deprecated", stacklevel=2)

from lms.djangoapps.badges.backends import *
