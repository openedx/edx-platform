import warnings
warnings.warn("Importing badges.events instead of lms.djangoapps.badges.events is deprecated", stacklevel=2)

from lms.djangoapps.badges.events import *
