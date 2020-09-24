import warnings
warnings.warn("Importing debug instead of lms.djangoapps.debug is deprecated", stacklevel=2)

from lms.djangoapps.debug import *
