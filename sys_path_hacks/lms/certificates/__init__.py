import warnings
warnings.warn("Importing certificates instead of lms.djangoapps.certificates is deprecated", stacklevel=2)

from lms.djangoapps.certificates import *
