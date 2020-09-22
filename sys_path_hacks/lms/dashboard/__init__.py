import warnings
warnings.warn("Importing dashboard instead of lms.djangoapps.dashboard is deprecated", stacklevel=2)

from lms.djangoapps.dashboard import *
