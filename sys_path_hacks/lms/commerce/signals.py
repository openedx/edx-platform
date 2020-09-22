import warnings
warnings.warn("Importing commerce.signals instead of lms.djangoapps.commerce.signals is deprecated", stacklevel=2)

from lms.djangoapps.commerce.signals import *
