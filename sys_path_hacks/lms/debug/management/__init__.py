import warnings
warnings.warn("Importing debug.management instead of lms.djangoapps.debug.management is deprecated", stacklevel=2)

from lms.djangoapps.debug.management import *
