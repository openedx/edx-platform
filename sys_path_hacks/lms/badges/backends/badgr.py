import warnings
warnings.warn("Importing badges.backends.badgr instead of lms.djangoapps.badges.backends.badgr is deprecated", stacklevel=2)

from lms.djangoapps.badges.backends.badgr import *
