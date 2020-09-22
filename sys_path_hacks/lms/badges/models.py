import warnings
warnings.warn("Importing badges.models instead of lms.djangoapps.badges.models is deprecated", stacklevel=2)

from lms.djangoapps.badges.models import *
