import warnings
warnings.warn("Importing mailing instead of lms.djangoapps.mailing is deprecated", stacklevel=2)

from lms.djangoapps.mailing import *
