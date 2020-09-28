import warnings
warnings.warn("Importing debug.views instead of lms.djangoapps.debug.views is deprecated", stacklevel=2)

from lms.djangoapps.debug.views import *
