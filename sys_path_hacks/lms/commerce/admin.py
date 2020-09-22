import warnings
warnings.warn("Importing commerce.admin instead of lms.djangoapps.commerce.admin is deprecated", stacklevel=2)

from lms.djangoapps.commerce.admin import *
