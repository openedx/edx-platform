import warnings
warnings.warn("Importing badges.apps instead of lms.djangoapps.badges.apps is deprecated", stacklevel=2)

from lms.djangoapps.badges.apps import *
