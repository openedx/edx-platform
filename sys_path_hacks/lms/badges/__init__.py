import warnings
warnings.warn("Importing badges instead of lms.djangoapps.badges is deprecated", stacklevel=2)

from lms.djangoapps.badges import *
