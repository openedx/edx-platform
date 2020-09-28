import warnings
warnings.warn("Importing branding instead of lms.djangoapps.branding is deprecated", stacklevel=2)

from lms.djangoapps.branding import *
