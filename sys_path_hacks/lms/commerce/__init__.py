import warnings
warnings.warn("Importing commerce instead of lms.djangoapps.commerce is deprecated", stacklevel=2)

from lms.djangoapps.commerce import *
