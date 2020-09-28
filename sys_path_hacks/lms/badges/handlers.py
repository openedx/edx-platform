import warnings
warnings.warn("Importing badges.handlers instead of lms.djangoapps.badges.handlers is deprecated", stacklevel=2)

from lms.djangoapps.badges.handlers import *
