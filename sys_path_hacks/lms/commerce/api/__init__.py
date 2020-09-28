import warnings
warnings.warn("Importing commerce.api instead of lms.djangoapps.commerce.api is deprecated", stacklevel=2)

from lms.djangoapps.commerce.api import *
