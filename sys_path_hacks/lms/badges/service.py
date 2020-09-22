import warnings
warnings.warn("Importing badges.service instead of lms.djangoapps.badges.service is deprecated", stacklevel=2)

from lms.djangoapps.badges.service import *
